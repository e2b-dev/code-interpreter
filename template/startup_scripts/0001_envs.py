import os
import IPython


class E2BEnviron(os._Environ):
    return_values = {}
    keys_to_remove = set()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.return_values.pop(key, None)
        self.keys_to_remove.discard(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.return_values.pop(key, None)
        self.keys_to_remove.discard(key)

    def set_envs_for_execution(self, update=None):
        update = update or {}

        return_values = {
            key: self[key] for key in set(self.keys()).intersection(update.keys())
        }
        keys_to_remove = set(update.keys()).difference(self.keys())

        self.update(update)

        self.return_values = return_values
        self.keys_to_remove = keys_to_remove

    def reset_envs_for_execution(self):
        for key in self.keys_to_remove:
            self.pop(key)
        self.update(self.return_values)
        self.keys_to_remove.clear()
        self.return_values.clear()


e2b_environ = E2BEnviron(
    {},
    os.environ.encodekey,
    os.environ.decodekey,
    os.environ.encodekey,
    os.environ.decodekey,
)
e2b_environ.update(os.environ)
os.environ = e2b_environ


def reset_envs(_):
    os.environ.reset_envs_for_execution()


ip = IPython.get_ipython()
ip.events.register("post_run_cell", reset_envs)
