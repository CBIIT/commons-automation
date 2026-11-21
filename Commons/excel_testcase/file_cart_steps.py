"""Shared Excel actions for portals that explicitly opt in to file carts."""


def file_cart_handlers():
    return {
        'open_cart_file_source': lambda app, _p, _a, _f, _e: app.file_cart.open_source(),
        'select_cart_files': lambda app, _p, count, _f, _e: app.file_cart.select_files(0 if count == 'all' else int(count or 3)),
        'next_cart_source_page': lambda app, _p, _a, _f, _e: app.file_cart.move_page('Next', source=True),
        'add_selected_files_to_cart': lambda app, _p, _a, _f, _e: app.file_cart.add_selected(),
        'open_file_cart': lambda app, _p, _a, _f, _e: app.file_cart.open(),
        'verify_file_cart': lambda app, _p, _a, _f, excel: app.file_cart.verify(excel),
        'verify_cart_persistence': lambda app, _p, _a, _f, excel: app.file_cart.verify_persistence(excel),
        'sort_file_cart': lambda app, _p, field, direction, _e: app.file_cart.verify_sort(field, direction),
        'set_cart_page_size': lambda app, _p, count, _f, _e: app.file_cart.set_page_size(int(count)),
    }



def c3dc_cart_handlers():
    return {
        **file_cart_handlers(),
        'verify_duplicate_cart_addition': lambda app, _p, _a, _f, _e: app.file_cart.verify_duplicate_addition(),
        'download_cart_manifest': lambda app, _p, _a, _f, excel: app.file_cart.download_manifest(excel),
        'verify_cart_manifest': lambda app, _p, _a, _f, _e: app.file_cart.verify_manifest(),
        'remove_cart_file': lambda app, _p, _a, _f, _e: app.file_cart.remove_one(),
        'remove_all_cart_files': _remove_all,
        'prepare_small_cart_filter': lambda app, _p, maximum, _f, _e: app.file_cart.prepare_small_filter(int(maximum or 25)),
        'add_all_filtered_files_to_cart': lambda app, _p, maximum, _f, _e: app.file_cart.add_all_filtered(int(maximum or 25)),
        'verify_empty_file_cart': lambda app, _p, _a, _f, excel: app.file_cart.verify_empty(excel),
        'verify_cart_static_content': lambda app, _p, _a, _f, _e: app.file_cart.verify_static(),
        'verify_cart_user_guide': lambda app, _p, _a, _f, _e: app.file_cart.verify_guide(),
        'verify_cart_cgc_entry': lambda app, _p, host, _f, _e: app.file_cart.verify_cgc_entry(host),
    }


def _remove_all(app, _page, decision, _filter, _excel):
    if decision not in ('confirm', 'cancel'):
        raise ValueError('Remove All decision must be confirm or cancel')
    app.file_cart.remove_all(decision == 'confirm')
