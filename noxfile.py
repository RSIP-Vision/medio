import nox

# Lookup table for valid (python, itk, numpy) combinations
COMPAT_MATRIX = {
    "3.9": [
        ("5.4.0", "1.24.4", None),
        ("5.4.0", "2.0.2", "5.3.0"),
        ("5.3.0", "1.24.4", None),
    ],
    "3.10": [
        ("5.4.0", "1.24.4", None),
        ("5.4.0", "2.2.6", "5.3.0"),
        ("5.3.0", "1.24.4", None),
    ],
    "3.11": [
        ("5.4.0", "1.24.4", None),
        ("5.4.0", "2.3.2", "5.3.0"),
        ("5.3.0", "1.24.4", None),
    ],
    "3.12": [
        ("5.4.0", "1.26.0", None),
        ("5.4.0", "2.3.2", "5.3.0"),
    ],
}

for py_ver, combos in COMPAT_MATRIX.items():
    if not combos:
        continue

    @nox.session(venv_backend="uv", python=py_ver, name=f"tests-py{py_ver.replace('.', '')}")
    @nox.parametrize("itk_version,numpy_version,nibabel_version", combos)
    def tests(session, itk_version, numpy_version, nibabel_version):
        verbosity = 'verbose' in session.posargs
        actual_version = session.run(
            "python", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
            silent=True
        ).strip()
        python = session.python
        if actual_version != python:
            session.error(f"Python interpreter mismatch: requested {python}, but running {actual_version}.\n"
                          f"Make sure python{python} is available in your PATH.")

        session.log(f"Testing with Python {python}, ITK {itk_version}, numpy {numpy_version}, nibabel {nibabel_version}")
        session.run_install(
            "uv",
            "sync",
            "--extra=test",
            f"--python={session.virtualenv.location}",
            env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        )
        pkgs = [f"itk=={itk_version}", f"numpy=={numpy_version}"]
        if nibabel_version:
            pkgs.append(f"nibabel=={nibabel_version}")
        session.install(*pkgs, silent=not verbosity)
        session.run("pytest")
    
