import torch
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.env_util import make_vec_env
from typing import Dict, Any

class TradingFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space):
        super().__init__(observation_space, features_dim=512)
        self.net = nn.Sequential(
            nn.Linear(observation_space.shape[0], 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.LayerNorm(512),
            nn.ReLU()
        )
    
    def forward(self, observations):
        return self.net(observations)

class ScalpingPPOAgent:
    def __init__(self, env_config: Dict[str, Any]):
        self.env = make_vec_env(
            lambda: TradingEnv(**env_config),
            n_envs=env_config.get('n_envs', 4)
        )
        
        policy_kwargs = {
            "features_extractor_class": TradingFeatureExtractor,
            "net_arch": [dict(pi=[256, 256], vf=[256, 256])],
            "activation_fn": nn.ReLU
        }
        
        self.model = PPO(
            "MlpPolicy",
            self.env,
            policy_kwargs=policy_kwargs,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=1,
            device='auto'
        )
        
    def train(self, total_timesteps: int = 1_000_000):
        self.model.learn(total_timesteps=total_timesteps)
        
    def predict(self, observation, deterministic=False):
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return self._process_action(action)
        
    def _process_action(self, raw_action):
        """Convert raw action to trading decision with SL/TP"""
        # Action space: [signal(0-1), stop_loss_pips(5-50), take_profit_pips(5-50), trailing_stop(0/1)]
        signal = 1 if raw_action[0] > 0.5 else -1
        stop_loss = max(5, min(50, raw_action[1] * 50))
        take_profit = max(5, min(50, raw_action[2] * 50))
        trailing_stop = raw_action[3] > 0.5
        
        return {
            'signal': signal,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'trailing_stop': trailing_stop
        }