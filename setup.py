from setuptools import setup, find_packages

setup(
    name="vical",
    version="0.1.0",
    description="Terminal-based calendar and task manager with Vi-like motions and commands.",
    author="Machoo",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "vical = vical.__main__:run",
        ],
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
