"""PPO eğitim scripti için birim testleri.

Eğitimin doğru çalıştığını, model dosyasının oluştuğunu
ve eğitilmiş modelin ortamda aksiyon üretebildiğini doğrular.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402


@pytest.fixture
def sample_prices() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.uniform(500.0, 4000.0, size=72).astype(np.float32)


@pytest.fixture
def trained_model(sample_prices, tmp_path):
    """1000 adım eğitilmiş küçük bir PPO modeli."""

    def make_env():
        return SmartHomeEnergyEnv(sample_prices, random_day=True)

    env = make_vec_env(make_env, n_envs=1, seed=0)
    model = PPO("MlpPolicy", env, verbose=0, seed=0)
    model.learn(total_timesteps=1000)
    model_path = tmp_path / "test_model"
    model.save(str(model_path))
    return model, str(model_path) + ".zip"


def test_ppo_trains_without_error(sample_prices) -> None:
    """PPO eğitimi hatasız tamamlanıyor mu?"""

    def make_env():
        return SmartHomeEnergyEnv(sample_prices, random_day=True)

    env = make_vec_env(make_env, n_envs=1, seed=0)
    model = PPO("MlpPolicy", env, verbose=0, seed=0)
    model.learn(total_timesteps=500)


def test_model_saves_and_loads(trained_model) -> None:
    """Model kaydedilip yüklenebiliyor mu?"""
    _, model_path = trained_model
    assert Path(model_path).exists()

    loaded = PPO.load(model_path)
    assert loaded is not None


def test_trained_model_produces_valid_actions(trained_model, sample_prices) -> None:
    """Eğitilmiş model geçerli aksiyon üretiyor mu?"""
    model, _ = trained_model
    env = SmartHomeEnergyEnv(sample_prices, random_day=False)
    obs, _ = env.reset(seed=0)

    action, _ = model.predict(obs, deterministic=True)

    assert action.shape == (1,)
    assert -1.0 <= float(action[0]) <= 1.0


def test_trained_model_completes_episode(trained_model, sample_prices) -> None:
    """Eğitilmiş model tam bir bölümü tamamlıyor mu?"""
    model, _ = trained_model
    env = SmartHomeEnergyEnv(sample_prices, random_day=False)
    obs, _ = env.reset(seed=0)

    terminated = False
    steps = 0
    total_reward = 0.0

    while not terminated:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1

    assert steps == 24
    assert np.isfinite(total_reward)
