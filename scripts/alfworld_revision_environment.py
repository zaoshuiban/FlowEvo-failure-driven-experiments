"""Load one preverified ALFWorld game without scanning other training tasks.

The caller must verify the frozen game/trajectory hashes and replay the original
checkpoint. Only dataset collection differs from StrictTrainEnv; the installed
AlfredTWEnv constructor and init_env, and the ordinary reset/step methods, remain
inherited and unmodified.
"""
from pathlib import Path

from alfworld_.success_baseline import StrictTrainEnv


class SelectedTrainEnv(StrictTrainEnv):
    def initialize(self, *, frozen_game_files: list[str] | None = None) -> int:
        if (not isinstance(frozen_game_files, list)
                or len(frozen_game_files) != 1
                or not isinstance(frozen_game_files[0], str)
                or not frozen_game_files[0]):
            raise ValueError("Exactly one frozen training game is required")

        # Validate only this selected path. Eligibility and content identities
        # come from the existing frozen checkpoint, never a dataset-wide scan.
        game = Path(frozen_game_files[0])
        train_root = (Path(self.alfworld_data) / "json_2.1.1" / "train").resolve()
        if (self.split != "train" or game.name != "game.tw-pddl"
                or not game.resolve().is_relative_to(train_root)
                or not game.is_file()):
            raise ValueError("Frozen game must be an existing official train game path")
        selected_files = tuple(frozen_game_files)

        from alfworld.agents.environment.alfred_tw_env import AlfredTWEnv

        class SelectedAlfredTWEnv(AlfredTWEnv):
            def collect_game_files(self, verbose=False):
                self.game_files = list(selected_files)
                self.num_games = len(self.game_files)

        config = self._build_config()
        tw_env = SelectedAlfredTWEnv(config, train_eval=self.split)
        self._env = tw_env.init_env(batch_size=1)
        self._initialized = True
        self._total_tasks = len(tw_env.game_files)
        self._task_index = 0
        return self._total_tasks
