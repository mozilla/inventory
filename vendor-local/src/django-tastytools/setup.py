from setuptools import setup, find_packages

setup(
    name="django-tastytools",
    version="0.1.0",
    packages = find_packages(),
    # packages=[
    #     "tastytools",
    #     "tastytools.test",
    #     "tastytools.test.definitions",
    #     "tastytools.api_doc",
    #     "tastytools.api_doc.templatetags",
    # ],
    package_data={
        'tastytools' : [
            '*.*',
        ]
    },
    include_package_data=True,
    long_description="Tools for django-tastypie autotesting and documentation.",
)

