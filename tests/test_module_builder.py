import io, zipfile
from jla.module_builder import build_module_zip

def test_builder():
    mid,blob=build_module_zip('Human Elephant Conflict','test')
    assert mid=='human_elephant_conflict'
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert f'{mid}/module.yaml' in z.namelist()
        assert f'{mid}/data/indicators.csv' in z.namelist()
