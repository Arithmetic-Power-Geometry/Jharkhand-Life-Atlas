import streamlit as st
from pathlib import Path
from jla.ui import hero
from jla.modules import discover_modules
from jla.data import module_indicators
hero("Modules", "JLA discovers module folders dynamically. Commit a new valid folder under modules/ and it appears here without changing navigation code.")
mods=[m for m in discover_modules() if not Path(m.get('_path','')).name.startswith('_')]
if not mods: st.warning('No modules discovered.')
for m in mods:
    with st.expander(f"{m.get('name')} · v{m.get('version')} · {m.get('status')}", expanded=m.get('id')=='core_geography'):
        st.write(m.get('description',''))
        if not m.get('_valid'): st.error('; '.join(m.get('_errors',[])))
        geo=m.get('geography',{}); st.caption(f"Primary geography: {geo.get('primary','—')} · Dependencies: {', '.join(m.get('dependencies',[])) or 'none'}")
        data=module_indicators(m.get('_path',''))
        if data is not None:
            try: empty=data.height==0
            except: empty=len(data)==0
            if empty: st.info('Module contract is active; no indicator observations have been published yet.')
            else: st.dataframe(data,width='stretch',hide_index=True)
