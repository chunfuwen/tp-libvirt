import os
import time
import glob

from virttest import installer

from avocado.utils import software_manager
from avocado.utils import build


def run(test, params, env):
    """
    Installs virtualization software using the selected installers

    :param test: test object.
    :param params: Dictionary with test parameters.
    :param env: Test environment.
    """
    srcdir = params.get("srcdir", test.srcdir)
    params["srcdir"] = srcdir

    # Flag if a installer minor failure occurred
    minor_failure = False
    minor_failure_reasons = []

    sm = software_manager.manager.SoftwareManager()

    for name in params.get("installers", "").split():
        installer_obj = installer.make_installer(name, params, test)
        if installer_obj.name == "ovirt_engine_sdk":
            installer_obj.install(
                cleanup=False, build=False, install=False)
            if installer_obj.minor_failure is True:
                minor_failure = True
                reason = "%s_%s: %s" % (installer_obj.name,
                                        installer_obj.mode,
                                        installer_obj.minor_failure_reason)
                minor_failure_reasons.append(reason)
            ovirt_src = os.path.join(srcdir, installer_obj.name)
            topdir = os.getcwd()
            os.chdir(ovirt_src)
            build.make("rpm")
            os.chdir(topdir)
            pkgs = glob.glob(
                os.path.join(ovirt_src, "rpmtop/RPMS/noarch/*"))
            for pkg in pkgs:
                sm.install(pkg)
        else:
            installer_obj.install(cleanup=False, build=False)
            time.sleep(5)
            if installer_obj.minor_failure is True:
                minor_failure = True
                reason = "%s_%s: %s" % (installer_obj.name,
                                        installer_obj.mode,
                                        installer_obj.minor_failure_reason)
                minor_failure_reasons.append(reason)
            env.register_installer(installer_obj)

    if minor_failure:
        test.warn("Minor (worked around) failures during build "
                  "test: %s" % ", ".join(minor_failure_reasons))
