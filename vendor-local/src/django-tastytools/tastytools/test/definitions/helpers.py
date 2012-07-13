def prepare_test_post_data(test, resource):
    post_data = resource.get_test_post_data()

    try:
        post_data = resource._meta.testdata.setup_post(test, post_data) or post_data
    except:
        pass

    return post_data
