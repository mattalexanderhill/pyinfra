'''
Manage dnf packages and repositories. Note that dnf package names are case-sensitive.
'''

from __future__ import unicode_literals

from pyinfra.api import operation

from . import files
from .util.packaging import ensure_packages, ensure_rpm, ensure_yum_repo


@operation
def key(state, host, key):
    '''
    Add dnf gpg keys with ``rpm``.

    + key: filename or URL

    Note:
        always returns one command, not state checking

    Example:

    .. code:: python

        dnf.key(
            {'Add the Docker CentOS gpg key'},
            'https://download.docker.com/linux/{{ host.fact.lsb_release.id|lower }}/gpg',
        )

    '''

    yield 'rpm --import {0}'.format(key)


@operation
def repo(
    state, host, name, baseurl,
    present=True, description=None, enabled=True, gpgcheck=True, gpgkey=None,
):
    '''
    Add/remove/update dnf repositories.

    + name: filename for the repo (in ``/etc/dnf/repos.d/``)
    + baseurl: the baseurl of the repo
    + present: whether the ``.repo`` file should be present
    + description: optional verbose description
    + gpgcheck: whether set ``gpgcheck=1``
    + gpgkey: the URL to the gpg key for this repo

    Example:

    .. code:: python

        dnf.repo(
            {'Add the Docker CentOS repo'},
            name='DockerCE',
            baseurl='https://download.docker.com/linux/centos/7/$basearch/stable',
        )
    '''

    yield from ensure_yum_repo(
        state, host, files,
        name, baseurl, present, description, enabled, gpgcheck, gpgkey,
    )


@operation
def rpm(state, host, source, present=True):
    '''
    Add/remove ``.rpm`` file packages.

    + source: filename or URL of the ``.rpm`` package
    + present: whether ore not the package should exist on the system

    URL sources with ``present=False``:
        If the ``.rpm`` file isn't downloaded, pyinfra can't remove any existing
        package as the file won't exist until mid-deploy.

    Example:

    .. code:: python

        dnf.rpm(
           {'Install EPEL rpm to enable EPEL repo'},
           'https://dl.fedoraproject.org/pub/epel/epel-release-latest-'
           '{{  host.fact.linux_distribution.major }}.noarch.rpm',
        )
    '''

    yield ensure_rpm(state, host, files, source, present, 'dnf')


@operation
def update(state, host):
    '''
    Updates all dnf packages.
    '''

    yield 'dnf update -y'

_update = update  # noqa: E305 (for use below where update is a kwarg)


@operation
def packages(
    state, host, packages=None,
    present=True, latest=False, update=False, clean=False, nobest=False,
    extra_install_args='', extra_uninstall_args='',
):
    '''
    Install/remove/update dnf packages & updates.

    + packages: list of packages to ensure
    + present: whether the packages should be installed
    + latest: whether to upgrade packages without a specified version
    + update: run dnf update
    + clean: run dnf clean
    + nobest: add the no best option to install
    + extra_install_args: additional arguments to the dnf install command
    + extra_uninstall_args: additional arguments to the dnf uninstall command

    Versions:
        Package versions can be pinned like dnf: ``<pkg>-<version>``

    Examples:

    .. code:: python

        # Update package list and install packages
        dnf.packages(
            {'Install Vim and Vim enhanced'},
            ['vim-enhanced', 'vim'],
            update=True,
        )

        # Install the latest versions of packages (always check)
        dnf.packages(
            {'Install latest Vim'},
            ['vim'],
            latest=True,
        )
    '''

    if clean:
        yield 'dnf clean all'

    if update:
        yield _update(state, host)

    nobest_option = ''
    if nobest:
        nobest_option = ' --nobest'

    if extra_install_args != '':
        extra_install_args = ' ' + extra_install_args

    if extra_uninstall_args != '':
        extra_uninstall_args = ' ' + extra_uninstall_args

    yield ensure_packages(
        packages, host.fact.rpm_packages, present,
        install_command='dnf install -y' + nobest_option + extra_install_args,
        uninstall_command='dnf remove -y' + extra_uninstall_args,
        upgrade_command='dnf update -y',
        version_join='-',
        latest=latest,
    )