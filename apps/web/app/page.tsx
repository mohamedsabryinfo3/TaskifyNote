'use client'
import {useState} from 'react'
const nav=['Dashboard','Tasks','Notes','Sources','AI Assistant','Settings']
const tasks=['Finish project proposal','Review saved article','Call Ahmed']
export default function Page(){
 const [active,setActive]=useState('Dashboard')
 return <main className="app-shell">
  <aside className="sidebar"><div className="logo">Taskify<span>Note</span></div><div className="nav">{nav.map(item=><button className={active===item?'nav-item active':'nav-item'} key={item} onClick={()=>setActive(item)}>{item}</button>)}</div><div className="sidebar-footer">Personal workspace<br/><small>v0.7.5</small></div></aside>
  <section className="main"><header className="top"><div><div className="eyebrow">PERSONAL WORKSPACE</div><h1>{active}</h1><p>Everything important, organized with AI.</p></div><button className="capture">＋ Capture</button></header>
   {active==='Dashboard'?<div className="dashboard">
    <section className="card welcome"><div><div className="pill">AI READY</div><h2>Good evening 👋</h2><p>Capture a link, organize a task, or ask your assistant anything.</p></div><div className="orb">AI</div></section>
    <section className="card"><div className="section-head"><h3>Today</h3><span>3 tasks</span></div>{tasks.map((t,i)=><div className="task" key={t}><span className={i===2?'check done':'check'}>✓</span><span className={i===2?'strike':''}>{t}</span><span className="task-meta">{i===0?'High':i===1?'Today':'Done'}</span></div>)}</section>
    <section className="card"><div className="section-head"><h3>Smart Capture</h3><span>URL → AI</span></div><div className="urlbox">https://example.com/article</div><button className="action">Analyze with AI</button></section>
    <section className="card"><div className="section-head"><h3>AI Assistant</h3><span>Private workspace</span></div><div className="chat-preview">“What should I work on today?”</div><p className="muted">Search tasks and notes semantically, summarize sources, and turn ideas into actions.</p></section>
   </div>:<section className="card single"><h2>{active}</h2><p className="muted">This module is ready to connect to the TaskifyNote API.</p></section>}
  </section>
 </main>
}
