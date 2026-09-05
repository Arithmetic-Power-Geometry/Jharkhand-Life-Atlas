import streamlit as st
from jla.ui import hero
from jla.security import admin_credentials, authenticate
from jla.module_builder import build_module_zip
from jla.validation import validate_core
hero("Admin", "Validate the platform and generate new module folders. Admin credentials are read from Streamlit Secrets and are never stored in the public repository.")
if 'admin_ok' not in st.session_state: st.session_state.admin_ok=False
expected_user, expected_pw=admin_credentials(st.secrets)
if not expected_user:
    st.warning('Admin mode is disabled until `[admin]` credentials are configured in Streamlit Secrets. Public mode remains fully functional.')
else:
    if not st.session_state.admin_ok:
        with st.form('login'):
            u=st.text_input('Username'); p=st.text_input('Password',type='password'); go=st.form_submit_button('Sign in',type='primary')
        if go:
            if authenticate(u,p,expected_user,expected_pw): st.session_state.admin_ok=True; st.rerun()
            else: st.error('Invalid credentials.')
    if st.session_state.admin_ok:
        top1,top2=st.columns([1,1])
        if top1.button('Run integrity checks'):
            errs=validate_core()
            if not errs:
                st.success('All core integrity checks passed.')
            else:
                st.error('\n'.join(errs))
        if top2.button('Sign out'): st.session_state.admin_ok=False; st.rerun()
        st.divider(); st.subheader('Module Builder')
        st.write('Create a module folder that can be committed directly under `modules/`. JLA discovers it automatically on the next deployment/restart.')
        with st.form('builder'):
            name=st.text_input('Module name',placeholder='Human–Elephant Conflict')
            desc=st.text_area('Description',placeholder='Event-level evidence for human–elephant interaction, risk and response.')
            geo=st.selectbox('Primary geography',['village','event','facility','district','grid','household_aggregate'])
            temporal=st.selectbox('Temporal type',['cross_sectional','time_series','event','versioned_reference'])
            make=st.form_submit_button('Build module ZIP',type='primary')
        if make and name.strip():
            mid,blob=build_module_zip(name,desc,geo,temporal)
            st.success(f'Module `{mid}` is valid and ready to add to GitHub.')
            st.download_button('Download module ZIP',blob,file_name=f'{mid}.zip',mime='application/zip')
            st.info('For permanent cloud deployment: unzip and commit the generated folder under `modules/`. Runtime filesystem uploads are intentionally not treated as permanent GitHub changes.')
