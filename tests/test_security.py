from jla.security import authenticate

def test_auth():
    assert authenticate('admin','x','admin','x')
    assert not authenticate('admin','bad','admin','x')
    assert not authenticate('admin','x',None,None)
