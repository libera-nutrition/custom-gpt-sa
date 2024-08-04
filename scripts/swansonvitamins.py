import datetime
import pathlib
import sys

import diskcache
import requests

FILE_PATH = pathlib.Path(__file__)
PACKAGE_PATH = FILE_PATH.parents[1]
DISKCACHE_PATH = PACKAGE_PATH / '.diskcache' / FILE_PATH.stem
DISKCACHE = diskcache.FanoutCache(directory=str(DISKCACHE_PATH), timeout=1, size_limit=1024 ** 3)


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_data')
def get_data(page_num: int, /) -> dict:
    response = requests.get('https://www.swansonvitamins.com/swanson-health-products', params={'page': page_num, 'json': True, 'items': 120})  # URL found via https://www.swansonvitamins.com/swanson-health-products
    try:
        response.raise_for_status()
    except Exception:
        print(f'Failed to get valid response for page {page_num}.', file=sys.stderr)
        raise

    try:
        data = response.json()
    except Exception:
        print(f'Failed to parse data for page {page_num}.', file=sys.stderr)
        raise
    print(f'Read data for page {page_num}.')
    return data


def main() -> None:
    final_results = set()
    page_num = 0
    while True:
        page_num += 1
        data = get_data(page_num)
        data = data['searchResultsDTO']
        curr_records = data['adobeRecords']
        print(f'Read page {page_num} with {len(curr_records)} records numbered {data['numRecordsFrom']}-{data['numRecordsTo']} out of {data['numRecordsTotal']}.')
        if not curr_records:
            break
        for record in curr_records:
            result = record['productName']
            if any(word.lower() in ('cats', 'dogs') for word in result.split(' ')):
                continue
            if (potency := record['productPotency']).upper() != 'SEE LABEL':
                result += f' ({potency})'
            final_results.add(result)

    output_results = sorted(final_results)
    output_text = '\n'.join(output_results)
    output_path = PACKAGE_PATH / 'uploads/SwansonVitamins_products_list.txt'
    print(f'Writing {len(output_results)} results having text length {len(output_text):,} to {output_path}.')
    output_path.write_text(output_text)


if __name__ == '__main__':
    main()
