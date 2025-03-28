import logging
import torch
import torch.optim as optim
import numpy as np
from collections import deque
import random
import gymnasium as gym
from gymnasium import spaces
from trading.rl.actor_critic import ActorCritic
from .utils import check_for_nans
from config.settings import settings
from trading.env import TradingEnv

logger = logging.getLogger(__name__)

class PPODQNAgent:
    def __init__(self, env: TradingEnv, lr=1e-4, gamma=0.99, clip_epsilon=0.2):
        self.env = env
        
        # Debug checks
        # Now safe to access shape
        # Handle observation space
        if not hasattr(env, 'observation_space'):
            raise AttributeError("Environment missing observation_space")
            
        if isinstance(env.observation_space, spaces.Dict):
            self.input_dim = env.observation_dim
        elif isinstance(env.observation_space, spaces.Box):
            self.input_dim = env.observation_space.shape[0]
        else:
            raise ValueError(f"Unsupported space: {type(env.observation_space)}")
        
        logger.info(f"Agent created with input_dim={self.input_dim}")
        self.policy = ActorCritic(self.input_dim, env.action_space.n)
        
        # Rest of initialization
        self.gamma = gamma
        self.clip_epsilon = clip_epsilon
        self.buffer = deque(maxlen=10000)
        self.policy = ActorCritic(self.input_dim, env.action_space.n)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.eps = 1e-8
        
    def _features_to_state(self, features: dict) -> torch.Tensor:
        """Convert market features to normalized state tensor"""
        state = np.array([
            features['mid_price'],
            features['spread'] * 10000,  # Convert to pips
            features['volatility'] * 10000,
            features['momentum'] * 10000,
            features['liquidity'],
            self.env.position_size / settings.DEFAULT_LOT_SIZE,
            self.env._calculate_pnl(features['mid_price'])
        ], dtype=np.float32)

        if state.shape[0] != self.input_dim:
            raise ValueError(
                f"State dimension mismatch. "
                f"Expected {self.input_dim}, got {state.shape[0]}"
            )
        
        return torch.FloatTensor(state)

    async def process_tick(self, features: dict):
        """Handle new market data and take trading action"""
        try:
            # Convert to state vector
            state = self._features_to_state(features)
            
            if check_for_nans(state, "state vector"):
                logger.warning("Invalid state detected, skipping tick")
                return
                
            # Get action from policy
            with torch.no_grad():
                probs, _ = self.policy(state)
                if check_for_nans(probs, "action probabilities"):
                    return
                    
                probs = torch.clamp(probs, min=self.eps, max=1.0-self.eps)
                probs = probs / probs.sum()
                
                dist = torch.distributions.Categorical(probs)
                action = dist.sample().item()
            
            # Execute action
            _, reward, done, _ = await self.env.step(action)
            
            # Store experience
            if not check_for_nans(torch.FloatTensor([reward]), "reward"):
                self.buffer.append((state.numpy(), action, reward, None, done))
            
        except Exception as e:
            logger.error(f"Error processing tick: {str(e)}", exc_info=True)
    
    async def train(self, n_episodes=1000, batch_size=64):
        """Training loop with experience replay"""
        for episode in range(n_episodes):
            state = await self.env.reset()
            episode_reward = 0
            
            while True:
                # Process current state
                state_tensor = torch.FloatTensor(state)
                probs, value = self.policy(state_tensor)

                if check_for_nans(probs, "action probabilities") or check_for_nans(value, "state value"):
                    state = await self.env.reset()
                    continue
                
                # Select action
                probs = torch.clamp(probs, min=self.eps, max=1.0-self.eps)
                probs = probs / probs.sum()
                dist = torch.distributions.Categorical(probs)
                action = dist.sample().item()
                
                # Take action
                next_state, reward, done, _ = await self.env.step(action)

                # Store experience
                if not check_for_nans(torch.FloatTensor([reward]), "reward"):
                    self.buffer.append((state, action, reward, next_state, done))
                episode_reward += reward
                
                # Train on batch
                if len(self.buffer) >= batch_size:
                    await self._update_policy(batch_size)
                
                if done:
                    logger.info(f"Episode {episode} reward: {episode_reward:.2f}")
                    break
                    
                state = next_state
    
    async def _update_policy(self, batch_size):
        """PPO policy update with experience replay"""
        if len(self.buffer) < batch_size:
            return
            
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)
        
        # Validate inputs
        if (check_for_nans(states, "states") or 
            check_for_nans(actions, "actions") or
            check_for_nans(rewards, "rewards")):
            return
        
        # Calculate advantages
        with torch.no_grad():
            _, next_values = self.policy(next_states)
            target_values = rewards + (1 - dones) * self.gamma * next_values.squeeze()
            _, current_values = self.policy(states)
            advantages = target_values - current_values.squeeze()
        
        # PPO policy loss
        new_probs, _ = self.policy(states)
        new_probs = new_probs.gather(1, actions.unsqueeze(1))
        old_probs = new_probs.detach()
        
        ratio = new_probs / old_probs
        clipped_ratio = torch.clamp(ratio, 1-self.clip_epsilon, 1+self.clip_epsilon)
        policy_loss = -torch.min(ratio * advantages.unsqueeze(1),
                               clipped_ratio * advantages.unsqueeze(1)).mean()
        
        # Value loss
        value_loss = (current_values.squeeze() - target_values).pow(2).mean()
        
        # Total loss
        loss = policy_loss + 0.5 * value_loss
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
        self.optimizer.step()