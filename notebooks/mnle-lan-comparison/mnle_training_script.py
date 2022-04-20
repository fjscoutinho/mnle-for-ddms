import pickle
import torch

from joblib import Parallel, delayed
from pathlib import Path
from sbi.inference import MNLE


BASE_DIR = Path(__file__).resolve().parent.parent.parent.as_posix()
data_folder = BASE_DIR + "/data/"
save_folder = BASE_DIR + "/notebooks/mnle-lan-comparison/models/"

def train_mnle(theta, x, num_simulations, seed):
    """Returns trained MNLE of type MixedNeuralLikelihoodEstimator (nn.Module)."""

    theta = theta[:num_simulations]
    x = x[:num_simulations]

    trainer = MNLE()
    estimator = trainer.append_simulations(theta, x).train()

    with open(save_folder + f"mnle_n{num_simulations}_seed{seed}.p", "wb") as fh:
        pickle.dump(dict(estimator=estimator, num_simulations=num_simulations), fh)

    return estimator

# Load pre-simulated training data
with open(data_folder + "ddm_training_and_test_data_10mio.p", "rb") as fh:
    theta, x_1d, test_x, test_thetas = pickle.load(fh).values()

# encode x as (time, choice)
x = torch.zeros((x_1d.shape[0], 2))
x[:, 0] = abs(x_1d[:, 0])
x[x_1d[:, 0] > 0, 1] = 1

num_workers = 10
num_repeats = 10
budgets = torch.tensor([10_000, 100_000, 1_000_000, 10_000_000]).repeat_interleave(num_repeats)
seeds = torch.randint(0, 1000000, size=(budgets.shape[0],))


results = Parallel(n_jobs=num_workers)(
    delayed(train_mnle)(theta, x, budget.item(), seed) for budget, seed in zip(budgets, seeds)
)