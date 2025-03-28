import torch
import torch.nn as nn
from ..rl.utils import check_for_nans

class ActorCritic(nn.Module):
    def __init__(self, input_dim, action_dim):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128)
        )
        self.actor = nn.Sequential(
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        self.critic = nn.Linear(128, 1)
        
    def forward(self, x):
        if check_for_nans(x, "network input"):
            # Return uniform probabilities and zero value if input is invalid
            actions = torch.ones(x.shape[0], self.action_dim) / self.action_dim
            value = torch.zeros(x.shape[0], 1)
            return actions, value

        features = self.shared(x)
        
        if check_for_nans(features, "shared features"):
            actions = torch.ones(x.shape[0], self.action_dim) / self.action_dim
            value = torch.zeros(x.shape[0], 1)
            return actions, value
 
        action_probs = self.actor(features)
        state_value = self.critic(features)
        
        return action_probs, state_value