'use strict';
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=n=>Number(n||0).toLocaleString('en-IN');
const money=n=>'₹'+Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:2,minimumFractionDigits:0});
const state={user:null,view:'overview',stats:null,lists:{},modal:null,search:''};
const meta={overview:['Overview','Your inventory operations at a glance'],products:['Inventory','Monitor stock, pricing and replenishment'],suppliers:['Suppliers','Manage your vendor network'],orders:['Purchase orders','Track and receive incoming purchases'],transactions:['Stock movements','Trace every warehouse adjustment'],employees:['Employees','Your pySupply team directory'],categories:['Categories','Organize your product catalog'],audit:['Audit activity','Changes and actions made in the workspace']};
const canWrite=()=>state.user&&['admin','manager'].includes(state.user.role);
const isAdmin=()=>state.user&&state.user.role==='admin';
const liveStatus=(status)=>({draft:'gray',submitted:'blue',received:'green',cancelled:'red',active:'green',inactive:'gray'}[status]||'gray');
const badge=(name,color)=>`<span class="badge ${color||liveStatus(name)}">${esc(name)}</span>`;
function toast(message,error=false){const el=document.createElement('div');el.className='toast'+(error?' error':'');el.textContent=message;$('#toastArea').appendChild(el);setTimeout(()=>el.remove(),3900)}
async function api(path,opt={}){
 const headers={...(opt.headers||{})};
 if(opt.body && typeof opt.body!=='string'){headers['Content-Type']='application/json';opt.body=JSON.stringify(opt.body)}
 if(opt.method&&opt.method!=='GET'){headers['X-CSRF-Token']=state.user?.csrf_token||''}
 const r=await fetch(path,{credentials:'same-origin',...opt,headers});
 if(r.status===401){location.href='/login';throw Error('Session expired')}
 const payload=await r.json().catch(()=>null);
 if(!r.ok)throw Error(payload?.detail||'Request failed');return payload;
}
async function fetchList(kind,force=false){if(force||!state.lists[kind])state.lists[kind]=await api(`/api/${kind}?limit=500`);return state.lists[kind]}
function invalidate(){state.lists={};state.stats=null}
function showShade(open){$('#sidebar').classList.toggle('open',open);$('#mobileShade').hidden=!open}
function nav(view){state.view=view;state.search='';document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('selected',x.dataset.view===view));$('#breadcrumbCurrent').textContent=meta[view][0];showShade(false);render().catch(e=>{console.error(e);toast(e.message,true)})}
function greeting(){return `<section class="welcome-row"><div><span class="eyebrow">OPERATIONS INTELLIGENCE</span><h1>Inventory overview <span class="heading-sparkle">✦</span></h1><p>Everything you need to run a smarter, more connected supply operation.</p></div>${canWrite()?`<button class="btn btn-primary" data-action="stock">＋ Stock movement</button>`:''}</section>`}
function kpi(label,value,icon,color,note){return `<article class="kpi-card"><div class="kpi-top"><span class="kpi-label">${label}</span><div class="kpi-icon ${color}">${icon}</div></div><div class="kpi-num">${value}</div><div class="kpi-meta">${note}</div></article>`}
function barChart(items){const max=Math.max(1,...items.map(x=>x.stock_units));return `<div class="chart-items">${items.map(x=>`<div class="bar-row"><span class="bar-label" title="${esc(x.name)}">${esc(x.name)}</span><progress class="bar-track" max="${max}" value="${x.stock_units}"></progress><strong class="bar-count">${num(x.stock_units)}</strong></div>`).join('')}</div>`}
async function renderOverview(){const s=state.stats||await api('/api/stats');state.stats=s;
 const orders=await fetchList('orders');const transactions=await fetchList('transactions');const products=await fetchList('products');
 const recent=orders.slice(0,6).map(o=>`<tr><td class="cell-primary">#${o.id}</td><td>${esc(o.product_name)}</td><td>${num(o.quantity)}</td><td>${badge(o.status)}</td></tr>`).join('');
 const movement=transactions.slice(0,5).map(t=>`<tr><td class="cell-primary">${esc(t.sku)}</td><td>${badge(t.kind,t.kind==='out'?'gold':'green')}</td><td>${t.change>0?'+':''}${t.change}</td><td>${num(t.balance_after)}</td></tr>`).join('');
 return `${greeting()}<div class="kpi-grid">${kpi('Total products',num(s.products),'▦','', 'Active products in your catalog')}${kpi('Available stock units',num(s.stock_units),'◫','blue','Across all warehouse items')}${kpi('Inventory value',money(s.stock_value),'₹','gold','Estimated at listed unit cost')}${kpi('Needs attention',num(s.low_stock),'⚑','red','Products at or below reorder level')}${kpi('Active suppliers',num(s.suppliers),'◇','', 'Connected business partners')}${kpi('Purchase orders',num(s.orders),'▤','blue',`${num(s.pending_orders)} awaiting completion`)}${kpi('Employees',num(s.employees),'♙','gold','Active pySupply team members')}${kpi('Product categories',num(s.categories),'⊞','', 'Across the product catalogue')}</div>
 <div class="dashboard-middle"><section class="panel"><div class="panel-header"><h2>Stock distribution by category</h2><small>Top categories by units</small></div><div class="panel-body">${barChart(s.categories_chart)}</div></section><section class="panel"><div class="panel-header"><h2>Purchase order snapshot</h2><small>Order pipeline</small></div><div class="panel-body"><div class="status-grid">${['draft','submitted','received','cancelled'].map(st=>{const entry=s.order_status.find(x=>x.status===st);return `<div class="status-item"><label>${st}</label><strong>${num(entry?.count||0)}</strong></div>`}).join('')}</div><p class="muted" style="font-size:12px;line-height:1.8;margin-top:22px">Track your orders from draft through receipt. Receiving an order adds the stock exactly once.</p><button class="btn btn-secondary btn-sm" data-go="orders">View purchase orders →</button></div></section></div>
 <div class="dashboard-bottom"><section class="panel"><div class="panel-header"><h2>Recent purchase orders</h2><button class="btn btn-secondary btn-sm" data-go="orders">View all →</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>PO ID</th><th>Product</th><th>Quantity</th><th>Status</th></tr></thead><tbody>${recent||'<tr><td colspan="4">No orders yet</td></tr>'}</tbody></table></div><div class="panel-header"><h2>Recent stock movements</h2><button class="btn btn-secondary btn-sm" data-go="transactions">See history →</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>SKU</th><th>Type</th><th>Change</th><th>Balance</th></tr></thead><tbody>${movement||'<tr><td colspan="4">No movements yet</td></tr>'}</tbody></table></div></section><section class="panel"><div class="panel-header"><h2>Low stock alerts</h2><span class="badge red">${s.low_stock} items</span></div><div class="low-stock-list">${s.low_stock_items.length?s.low_stock_items.map(p=>`<div class="low-stock-item"><div><strong>${esc(p.name)}</strong><small>${esc(p.sku)}</small></div><span class="low-stock-qty">${num(p.quantity)} / ${num(p.reorder_level)}</span></div>`).join(''):'<div class="empty-state">All products are above reorder level.</div>'}</div></section></div>`;
}
const columns={
 products:[['sku','SKU'],['name','Product'],['category_name','Category'],['supplier_name','Supplier'],['quantity','On hand'],['reorder_level','Reorder'],['unit_price','Unit price'],['active','Status']],
 suppliers:[['name','Supplier name'],['email','Contact email'],['phone','Phone'],['active','Status']],
 orders:[['id','Order'],['product_name','Product'],['supplier_name','Supplier'],['quantity','Quantity'],['unit_cost','Unit cost'],['status','Status']],
 transactions:[['id','Transaction'],['sku','SKU'],['kind','Type'],['change','Change'],['balance_after','Balance'],['note','Note'],['created_at','Date']],
 employees:[['employee_code','Employee ID'],['first_name','Employee'],['email','Work email'],['department','Department'],['job_title','Job title'],['status','Status']],
 categories:[['name','Category'],['active','Status']],
 audit:[['created_at','Date'],['actor','Actor'],['action','Action'],['detail','Details']]};
function valueFor(kind,col,item){if(kind==='employees'&&col==='first_name')return `<strong class="cell-primary">${esc(item.first_name)} ${esc(item.last_name)}</strong>`;
 if(col==='active')return badge(item.active?'Active':'Inactive',item.active?'green':'gray');
 if(col==='status')return badge(item.status);if(col==='kind')return badge(item.kind,item.kind==='out'?'gold':'green');
 if(['quantity','balance_after','reorder_level'].includes(col))return num(item[col]);
 if(['unit_price','unit_cost'].includes(col))return money(item[col]);
 if(col==='name'||col==='sku'||col==='employee_code')return `<strong class="cell-primary">${esc(item[col])}</strong>`;
 if(col==='change')return (item[col]>0?'+':'')+num(item[col]);
 if(col==='id')return '#'+esc(item.id);
 if(col==='created_at')return esc(String(item.created_at||'').slice(0,16).replace('T',' '));
 return esc(item[col]);}
function actionsFor(kind,item){if(!canWrite())return '';
 const editKinds=['products','suppliers','employees','categories'];const buttons=[];
 if(editKinds.includes(kind)&&(kind!=='categories'||isAdmin()))buttons.push(`<button class="table-action" data-action="edit" data-kind="${kind}" data-id="${item.id}">Edit</button>`);
 if(kind==='orders'&&item.status==='draft')buttons.push(`<button class="table-action" data-action="orderstatus" data-id="${item.id}" data-status="submitted">Submit</button>`);
 if(kind==='orders'&&item.status==='submitted')buttons.push(`<button class="table-action" data-action="orderstatus" data-id="${item.id}" data-status="received">Receive</button>`);
 if(kind==='orders'&&['draft','submitted'].includes(item.status))buttons.push(`<button class="table-action danger" data-action="orderstatus" data-id="${item.id}" data-status="cancelled">Cancel</button>`);
 if(isAdmin()&&editKinds.includes(kind)&&(kind!=='employees'?item.active:item.status==='active'))buttons.push(`<button class="table-action danger" data-action="archive" data-kind="${kind}" data-id="${item.id}">Deactivate</button>`);
 return buttons.join(' ');
}
function tableRows(kind,all){const q=state.search.trim().toLowerCase();const filtered=q?all.filter(x=>Object.values(x).some(v=>String(v??'').toLowerCase().includes(q))):all;
 const headers=columns[kind]||[];
 $('#rowCount').textContent=`Showing ${filtered.length} of ${all.length} records`;
 $('#tableBody').innerHTML=filtered.map(item=>`<tr>${headers.map(([key])=>`<td>${valueFor(kind,key,item)}</td>`).join('')}${canWrite()?`<td>${actionsFor(kind,item)}</td>`:''}</tr>`).join('')||`<tr><td colspan="${headers.length+1}"><div class="empty-state">No matching records found.</div></td></tr>`;
}
async function renderTable(kind){const rows=await fetchList(kind);
 const labels={products:'Add product',suppliers:'Add supplier',orders:'Create order',transactions:'Record stock',employees:'Add employee',categories:'Add category'};
 const btn=canWrite()&&labels[kind]&&(kind!=='categories'||isAdmin());
 const cols=columns[kind];const file=kind==='audit'?'':`<a class="btn btn-secondary" href="/api/export/${kind}">↓ Export CSV</a>`;
 $('#content').innerHTML=`<section class="page-title"><div><span class="eyebrow">PYSUPPLY OPERATIONS</span><h1>${esc(meta[kind][0])}</h1><p>${esc(meta[kind][1])}</p></div><div class="page-actions">${file}${btn?`<button class="btn btn-primary" data-action="${kind==='transactions'?'stock':'create'}" data-kind="${kind}">＋ ${labels[kind]}</button>`:''}</div></section><section class="data-panel"><div class="data-tools"><input aria-label="Search records" id="tableSearch" class="search-field" placeholder="⌕ Search ${esc(meta[kind][0].toLowerCase())}..." autocomplete="off"><span class="result-count" id="rowCount"></span></div><div class="table-wrap"><table class="data-table"><thead><tr>${cols.map(c=>`<th>${c[1]}</th>`).join('')}${canWrite()?'<th>Actions</th>':''}</tr></thead><tbody id="tableBody"></tbody></table></div></section>`;
 $('#tableSearch').addEventListener('input',e=>{state.search=e.target.value;tableRows(kind,rows)});
 tableRows(kind,rows);
}
async function render(){if(state.view==='audit'&&!isAdmin()){nav('overview');return}$('#content').innerHTML='<div class="loading-state">Loading records…</div>';if(state.view==='overview')$('#content').innerHTML=await renderOverview();else await renderTable(state.view)}
const opts=(rows,display,selected)=>rows.map(x=>`<option value="${x.id}" ${String(selected)===String(x.id)?'selected':''}>${esc(display(x))}</option>`).join('');
function field(name,label,type='text',value='',other=''){
 return `<div class="form-field ${other.includes('full')?'full':''}"><label for="m_${name}">${esc(label)}</label><input class="field" id="m_${name}" name="${esc(name)}" type="${type}" value="${esc(value)}" ${other.includes('required')?'required':''} ${type==='number'?'min="0" step="'+(name==='unit_price'||name==='unit_cost'?'0.01':'1')+'"':''}></div>`;
}
function selectField(name,label,choices,selected){return `<div class="form-field"><label for="m_${name}">${label}</label><select class="field" id="m_${name}" name="${name}">${opts(choices,x=>x.name||x.label||x.value,selected)}</select></div>`}
async function openModal(action,kind=null,item=null){if(!canWrite())return;let title='';let fields='';let endpoint='';let method='POST';let confirmed=false;
 const categories=await fetchList('categories');const suppliers=await fetchList('suppliers');const products=await fetchList('products');
 if(action==='stock'){
    title='Record stock movement';endpoint='/api/stock';
    fields=selectField('product_id','Select product',products.map(p=>({id:p.id,name:p.sku+' · '+p.name})))+
     selectField('kind','Movement type',[{id:'in',name:'Stock in'},{id:'out',name:'Stock out'},{id:'adjust',name:'Set actual quantity'}])+
     field('quantity','Quantity','number','1','required')+field('note','Reason / reference','text','','full');
 }else{
    const edit=action==='edit';kind=kind||state.view;endpoint='/api/'+(kind==='orders'?'orders':kind)+(edit?'/'+item.id:'');method=edit?'PUT':'POST';
    title=(edit?'Edit ':'Add ')+({products:'product',suppliers:'supplier',categories:'category',employees:'employee',orders:'purchase order'}[kind]||'record');
    const d=item||{};
    if(kind==='products')fields=field('sku','Product SKU','text',d.sku,'required')+field('name','Product name','text',d.name,'required full')+
       selectField('category_id','Category',categories.filter(x=>x.active||x.id===d.category_id),d.category_id)+selectField('supplier_id','Supplier',suppliers.filter(x=>x.active||x.id===d.supplier_id),d.supplier_id)+
       field('reorder_level','Reorder level','number',d.reorder_level??10,'required')+field('unit_price','Unit price (INR)','number',d.unit_price??100,'required');
    else if(kind==='suppliers')fields=field('name','Supplier company name','text',d.name,'required full')+field('email','Contact email','email',d.email,'full')+field('phone','Phone number','text',d.phone);
    else if(kind==='categories')fields=field('name','Category name','text',d.name,'required full');
    else if(kind==='employees')fields=field('employee_code','Employee ID','text',d.employee_code||`PYS-EMP-${Math.floor(Date.now()%100000)}`,'required')+field('first_name','First name','text',d.first_name,'required')+field('last_name','Last name','text',d.last_name,'required')+field('email','Work email','email',d.email,'required full')+field('department','Department','text',d.department||'Procurement','required')+field('job_title','Job title','text',d.job_title||'Specialist','required')+field('phone','Phone','text',d.phone)+field('joining_date','Joining date','date',d.joining_date||new Date().toISOString().slice(0,10),'required')+selectField('status','Status',[{id:'active',name:'Active'},{id:'inactive',name:'Inactive'}],d.status||'active');
    else if(kind==='orders'){
      const active=products.filter(p=>p.active);fields=selectField('product_id','Product',active.map(p=>({id:p.id,name:p.sku+' · '+p.name})))+selectField('supplier_id','Supplier',suppliers.filter(s=>s.active))+
       field('quantity','Ordered quantity','number','10','required')+field('unit_cost','Unit cost (INR)','number','1000','required');
    }
 }
 if(!fields)return toast('No form available for this item.',true);
 state.modal={endpoint,method,action,kind};$('#modalTitle').textContent=title;$('#modalFields').innerHTML=fields;
 $('#actionModal').showModal();
 if(kind==='employees'&&!item){const first=$('#m_first_name'),last=$('#m_last_name'),email=$('#m_email');const sync=()=>{if(!email.dataset.modified){email.value=(first.value+'.'+last.value).toLowerCase().replace(/[^a-z.]/g,'')+'@pysupply.com'}};first.addEventListener('input',sync);last.addEventListener('input',sync);email.addEventListener('input',()=>email.dataset.modified='1')}
 if(kind==='orders'){
    const product=$('#m_product_id');const supplier=$('#m_supplier_id');const cost=$('#m_unit_cost');
    const match=()=>{const p=products.find(x=>String(x.id)===product.value);if(p){supplier.value=String(p.supplier_id);cost.value=p.unit_price}};
    product.addEventListener('change',match);match();
 }
}
async function handleClick(e){const el=e.target.closest('[data-action], [data-go]');if(!el)return;
 if(el.dataset.go){nav(el.dataset.go);return}
 const action=el.dataset.action;
 try{
 if(action==='stock'){await openModal('stock');return}
 if(action==='create'){await openModal('create',el.dataset.kind);return}
 if(action==='edit'){const kind=el.dataset.kind;const item=(await fetchList(kind)).find(x=>String(x.id)===el.dataset.id);if(item)await openModal('edit',kind,item);return}
 if(action==='archive'){
    if(!confirm('Deactivate this record? Existing history will be preserved.'))return;
    await api(`/api/${el.dataset.kind}/${el.dataset.id}`,{method:'DELETE'});invalidate();toast('Record deactivated successfully');await render();return
 }
 if(action==='orderstatus'){
    if(!confirm(`Change this purchase order to "${el.dataset.status}"?`))return;
    await api(`/api/orders/${el.dataset.id}/status`,{method:'POST',body:{status:el.dataset.status}});invalidate();toast('Purchase order updated');await render();return;
 }
 }catch(err){toast(err.message,true)}
}
async function saveForm(e){e.preventDefault();if(!state.modal)return;
 const b=$('#saveModal');b.disabled=true;b.textContent='Saving…';
 try{
    const raw=Object.fromEntries(new FormData($('#actionForm')));
    for(const k of ['category_id','supplier_id','product_id','quantity','reorder_level','unit_price','unit_cost'])if(k in raw)raw[k]=Number(raw[k]);
    await api(state.modal.endpoint,{method:state.modal.method,body:raw});
    $('#actionModal').close();invalidate();toast('Saved successfully');await render();
 }catch(err){toast(err.message,true)}finally{b.disabled=false;b.textContent='Save record'}
}
async function start(){
 try{state.user=await api('/api/me')}catch{return}
 $('#userName').textContent=state.user.email;$('#userRole').textContent=state.user.role;
 document.querySelectorAll('.admin-only').forEach(x=>x.hidden=!isAdmin());
 document.querySelectorAll('.nav-button').forEach(b=>b.addEventListener('click',()=>nav(b.dataset.view)));
 $('#content').addEventListener('click',handleClick);$('#menuToggle').addEventListener('click',()=>showShade(true));$('#mobileShade').addEventListener('click',()=>showShade(false));
 $('#closeModal').addEventListener('click',()=>$('#actionModal').close());$('#cancelModal').addEventListener('click',()=>$('#actionModal').close());
 $('#actionForm').addEventListener('submit',saveForm);
 $('#logoutBtn').addEventListener('click',async()=>{try{await fetch('/logout',{method:'POST',credentials:'same-origin',headers:{'X-CSRF-Token':state.user.csrf_token}})}finally{location.href='/login'}});
 await render();
}
start().catch(e=>toast(e.message,true));
