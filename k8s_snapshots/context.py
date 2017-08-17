import os
import pykube
from importlib import import_module
import structlog


_logger = structlog.get_logger()


class Context:
    def __init__(self, config=None):
        self.config = config
        self._kube_config = None
        self._backend = None

    @property
    def kube_config(self):
        if self._kube_config is None:
            self._kube_config = self.load_kube_config()

        return self._kube_config

    @property
    def backend(self):
        if self._backend is None:
            module_name = {
                'google': 'google'
            }[self.config.get('cloud_provider')]
            self._backend = import_module('k8s_snapshots.backends.%s' % module_name)
        return self._backend

    def load_kube_config(self):
        cfg = None

        kube_config_file = self.config.get('kube_config_file')

        if kube_config_file:
            _logger.info('kube-config.from-file', file=kube_config_file)
            cfg = pykube.KubeConfig.from_file(kube_config_file)

        if not cfg:
            # See where we can get it from.
            default_file = os.path.expanduser('~/.kube/config')
            if os.path.exists(default_file):
                _logger.info(
                    'kube-config.from-file.default',
                    file=default_file)
                cfg = pykube.KubeConfig.from_file(default_file)

        # Maybe we are running inside Kubernetes.
        if not cfg:
            _logger.info('kube-config.from-service-account')
            cfg = pykube.KubeConfig.from_service_account()

        return cfg

    def kube_client(self):
        return pykube.HTTPClient(self.kube_config)


