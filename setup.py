from setuptools import setup, find_packages
import os

# Leer README
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = (
        "Automatización para descarga y procesamiento de dumps desde Google Drive para conversión Oracle a MongoDB"
    )

# Dependencias principales
install_requires = [
    "google-api-python-client>=2.0.0",
    "google-auth>=2.0.0",
    "google-auth-oauthlib>=0.5.0",
]

setup(
    name="hanapacha",
    version="0.1.6",
    author="Esteban Cossio",
    author_email="estebancogo47@gmail.com",
    description="Automatización para descarga y procesamiento de dumps desde Google Drive para conversión Oracle a MongoDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/C0SS10/hanapacha",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "MongoDB :: Software Development :: Scienti :: Colav :: ImpactU",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "hanapacha=hanapacha.cli:main",
        ],
    },
    include_package_data=True,
)
