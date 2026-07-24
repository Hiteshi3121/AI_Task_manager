import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'
import { fetchTasks, createTask, updateTask, deleteTask, fetchStudents, createStudent, updateStudent, fetchBrief, fetchPeople, createPerson, updatePerson, deletePerson, fetchCalendarStatus, openCalendarAuth, disconnectCalendar, fetchAnalytics, transcribeAudio, createManualTask, fetchCustomBuckets, createBucketInDB, deleteBucketFromDB } from './lib/api'

const BUCKETS = [
  { id: 'udukku',         label: 'Udukku',                            color: '#185FA5', bg: '#E6F1FB' },
  { id: 'ascend_social',  label: 'Ascend Now — Social Media',          color: '#3B6D11', bg: '#EAF3DE' },
  { id: 'ascend_classes', label: 'Ascend Now — Entrepreneurship Classes', color: '#993556', bg: '#FBEAF0' },
  { id: 'music',          label: 'My Music',                           color: '#534AB7', bg: '#EEEDFE' },
  { id: 'social_brand',   label: 'My Social Media',                    color: '#854F0B', bg: '#FAEEDA' },
  { id: 'fitness',        label: 'Fitness — Hyrox Prep',               color: '#993C1D', bg: '#FAECE7' },
  { id: 'personal',       label: 'Personal / Errands',                 color: '#555555', bg: '#EFEFEF' },
]

// Placement in the 3x3 grid around the centered capture bar.
// Udukku is the only bucket spanning two rows — it's the busiest board —
// which is what leaves exactly one free cell (center, row 2) for capture.
const GRID_PLACEMENT = {
  udukku: { column: 1, row: '1 / span 3' },
  // all other buckets auto-flow so vacant slots are filled automatically
}

const SUB_BUCKETS = {
  music_room:  'Music room',
  marketing:   'Marketing',
  operations:  'Operations',
  partnerships:'Partnerships',
  content:     'Content',
}

const PRIORITY_COLOR = { high: '#E24B4A', medium: '#EF9F27', low: '#639922' }

const DUE_PRESETS = ['today', 'this week', 'upcoming', 'no deadline', 'overdue']

function formatDueDate(iso) {
  return new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
}

// datetime-local inputs want "YYYY-MM-DDTHH:mm" in local time, with no
// timezone suffix — toISOString() is UTC, so this builds it from local
// getters instead of slicing the ISO string (which would shift the hour).
function toDatetimeLocalValue(iso) {
  const d = iso ? new Date(iso) : new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const STUDENT_STATUSES = [
  { id: 'not_started', label: 'Not started', color: '#777',    bg: '#f0f0f0' },
  { id: 'in_progress',  label: 'In progress', color: '#185FA5', bg: '#E6F1FB' },
  { id: 'on_hold',      label: 'On hold',     color: '#854F0B', bg: '#FAEEDA' },
  { id: 'completed',    label: 'Completed',   color: '#3B6D11', bg: '#EAF3DE' },
  { id: 'cancelled',    label: 'Cancelled',   color: '#993C1D', bg: '#FAECE7' },
]
const STATUS_BY_ID = Object.fromEntries(STUDENT_STATUSES.map(s => [s.id, s]))

const card = { background: 'white', border: '1px solid #e5e5e5', borderRadius: 12 }

function MicIcon({ size = 15, color = '#666' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
  )
}

function CheckIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="12" fill="#22C55E"/>
      <polyline points="6,12 10,16 18,8" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function XIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="12" fill="#F87171"/>
      <line x1="8" y1="8" x2="16" y2="16" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="16" y1="8" x2="8" y2="16" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}

// ---------- Task card ----------
function TaskCard({ task, onDone, onDelete, onUpdateDue, onUpdateTitle, bucketId, people, assignee, onUpdateAssignee }) {
  const [pickingDate, setPickingDate] = useState(false)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState(task.title)
  const [editingAssignee, setEditingAssignee] = useState(false)
  const isOverdue = task.due === 'overdue'
  const isCustom = task.due === 'custom'
  const daysOpen = Math.floor((Date.now() - new Date(task.created_at)) / 86400000)
  const isStaleOverdue = isOverdue && daysOpen >= 3

  function saveTitle() {
    setEditingTitle(false)
    if (titleDraft.trim() && titleDraft.trim() !== task.title) {
      onUpdateTitle(task.id, titleDraft.trim())
    } else {
      setTitleDraft(task.title)
    }
  }

  function handleSelectChange(value) {
    if (value === 'custom') {
      setPickingDate(true)
    } else {
      onUpdateDue(task.id, value)
    }
  }

  function handleDateConfirm(e) {
    const value = e.target.value
    setPickingDate(false)
    if (value) onUpdateDue(task.id, 'custom', new Date(value).toISOString())
  }

  const currentAssignee = assignee || 'Ishita'
  const peopleNames = ['Ishita', ...(people || []).map(p => p.name).filter(n => n !== 'Ishita')]

  return (
    <div style={{ padding: '7px 9px', background: isStaleOverdue ? '#fff8f8' : '#fafafa', borderRadius: 8, marginBottom: 6, borderLeft: `3px solid ${isStaleOverdue ? '#E24B4A' : PRIORITY_COLOR[task.priority]}`, outline: isStaleOverdue ? '1px solid #fcc' : 'none' }}>
      {task.sub_bucket_id && <p style={{ margin: '0 0 3px', fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{SUB_BUCKETS[task.sub_bucket_id]}</p>}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {editingTitle ? (
          <input
            autoFocus
            value={titleDraft}
            onChange={e => setTitleDraft(e.target.value)}
            onBlur={saveTitle}
            onKeyDown={e => { if (e.key === 'Enter') saveTitle(); if (e.key === 'Escape') { setTitleDraft(task.title); setEditingTitle(false) } }}
            style={{ flex: 1, fontSize: 12.5, border: 'none', borderBottom: '1px solid #185FA5', outline: 'none', background: 'transparent', padding: '0 2px' }}
          />
        ) : (
          <p
            onClick={() => setEditingTitle(true)}
            title="Click to edit"
            style={{ margin: 0, fontSize: 12.5, lineHeight: 1.4, flex: 1, cursor: 'text' }}
          >
            {task.title}
            {isStaleOverdue && <span title={`Overdue for ${daysOpen} days`} style={{ marginLeft: 5, fontSize: 10, fontWeight: 600, color: '#E24B4A' }}>⚠️ {daysOpen}d</span>}
          </p>
        )}

        {pickingDate ? (
          <input
            type="datetime-local"
            autoFocus
            defaultValue={toDatetimeLocalValue(task.due_date)}
            onBlur={handleDateConfirm}
            onKeyDown={e => { if (e.key === 'Enter') e.target.blur() }}
            style={{ fontSize: 9.5, padding: '1px 2px', borderRadius: 6, border: '1px solid #ccc', flexShrink: 0, maxWidth: 120 }}
          />
        ) : isCustom ? (
          <button
            onClick={() => setPickingDate(true)}
            title="Click to change the date"
            style={{
              fontSize: 9, fontWeight: 600, padding: '1px 5px', borderRadius: 10, flexShrink: 0, border: 'none', cursor: 'pointer',
              color: isOverdue ? '#A32D2D' : '#0C447C', background: isOverdue ? '#FCEBEB' : '#E6F1FB', whiteSpace: 'nowrap',
            }}
          >{task.due_date ? formatDueDate(task.due_date) : 'custom'}</button>
        ) : (
          <select
            value={task.due}
            onChange={e => handleSelectChange(e.target.value)}
            title="Deadline"
            style={{
              fontSize: 9, fontWeight: 600, padding: '1px 2px', borderRadius: 10, flexShrink: 0, border: 'none', cursor: 'pointer',
              color: isOverdue ? '#A32D2D' : '#888',
              background: isOverdue ? '#FCEBEB' : '#eee',
              maxWidth: 72,
            }}
          >
            {DUE_PRESETS.map(d => <option key={d} value={d}>{d}</option>)}
            <option value="custom">Custom…</option>
          </select>
        )}

        <div style={{ display: 'flex', gap: 4, flexShrink: 0, alignItems: 'center' }}>
          {task.calendar_event_id && <span title="Added to Google Calendar" style={{ fontSize: 11 }}>📅</span>}
          {bucketId === 'udukku' && (
            editingAssignee ? (
              <select
                autoFocus
                value={currentAssignee}
                onChange={e => { onUpdateAssignee(task.id, e.target.value); setEditingAssignee(false) }}
                onBlur={() => setEditingAssignee(false)}
                style={{ fontSize: 9, padding: '1px 2px', borderRadius: 8, border: '1px solid #185FA5', cursor: 'pointer', background: '#E6F1FB', color: '#185FA5', fontWeight: 600, maxWidth: 70 }}
              >
                {peopleNames.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            ) : (
              <button
                onClick={() => setEditingAssignee(true)}
                title="Assigned to — click to change"
                style={{ fontSize: 9, padding: '1px 5px', borderRadius: 8, border: 'none', cursor: 'pointer', background: '#E6F1FB', color: '#185FA5', fontWeight: 600, maxWidth: 70, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              >{currentAssignee}</button>
            )
          )}
          <button onClick={() => onDone(task.id, task.done)} title="Mark done" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}><CheckIcon /></button>
          <button onClick={() => onDelete(task.id)} title="Delete task" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}><XIcon /></button>
        </div>
      </div>
    </div>
  )
}

// ---------- Student roster card ----------
function StudentRow({ student, onUpdate }) {
  const [editingProject, setEditingProject] = useState(false)
  const [projectDraft, setProjectDraft] = useState(student.current_project || '')
  const status = STATUS_BY_ID[student.status] || STATUS_BY_ID.not_started

  function saveProject() {
    setEditingProject(false)
    if (projectDraft !== (student.current_project || '')) {
      onUpdate(student.id, { current_project: projectDraft || null })
    }
  }

  return (
    <div style={{ padding: '6px 8px', background: '#fafafa', borderRadius: 8, marginBottom: 6 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
        <p style={{ margin: 0, fontSize: 12, fontWeight: 600 }}>{student.name}</p>
        <select
          value={student.status}
          onChange={e => onUpdate(student.id, { status: e.target.value })}
          style={{ fontSize: 10, padding: '2px 4px', borderRadius: 6, border: 'none', background: status.bg, color: status.color, fontWeight: 600, cursor: 'pointer' }}
        >
          {STUDENT_STATUSES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
      </div>
      {editingProject ? (
        <input
          autoFocus
          value={projectDraft}
          onChange={e => setProjectDraft(e.target.value)}
          onBlur={saveProject}
          onKeyDown={e => { if (e.key === 'Enter') saveProject() }}
          placeholder="Set project..."
          style={{ width: '100%', fontSize: 11, padding: '3px 5px', marginTop: 3, border: '1px solid #ddd', borderRadius: 5, outline: 'none' }}
        />
      ) : (
        <p
          onClick={() => setEditingProject(true)}
          style={{ margin: '2px 0 0', fontSize: 11, color: student.current_project ? '#666' : '#aaa', cursor: 'pointer' }}
          title="Click to edit"
        >
          {student.current_project || 'Click to set project...'}
        </p>
      )}
      {student.next_follow_up && <p style={{ margin: '2px 0 0', fontSize: 11, color: '#999' }}>Next: {student.next_follow_up}</p>}
    </div>
  )
}

// ---------- Person card ----------
function PersonCard({ person, onDelete, onUpdatePerson, onAddTask }) {
  const [editingName, setEditingName] = useState(false)
  const [nameDraft, setNameDraft] = useState(person.name)
  const [editingRole, setEditingRole] = useState(false)
  const [roleDraft, setRoleDraft] = useState(person.role || '')
  const [showAddTask, setShowAddTask] = useState(false)
  const [taskDraft, setTaskDraft] = useState('')

  function saveName() {
    setEditingName(false)
    const val = nameDraft.trim() || person.name
    setNameDraft(val)
    if (val !== person.name) onUpdatePerson(person.id, { name: val })
  }

  function saveRole() {
    setEditingRole(false)
    const val = roleDraft.trim()
    if (val !== (person.role || '')) onUpdatePerson(person.id, { role: val })
  }

  function submitTask() {
    if (!taskDraft.trim()) return
    onAddTask(person.id, taskDraft.trim())
    setTaskDraft('')
    setShowAddTask(false)
  }

  const openTasks = (person.tasks || []).filter(t => !t.done)
  const avatar = person.name[0]?.toUpperCase()

  return (
    <div style={{ background: 'white', border: '1px solid #e5e5e5', borderRadius: 12, padding: '14px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#E6F1FB', color: '#185FA5', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{avatar}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          {editingName ? (
            <input
              autoFocus
              value={nameDraft}
              onChange={e => setNameDraft(e.target.value)}
              onBlur={saveName}
              onKeyDown={e => { if (e.key === 'Enter') saveName(); if (e.key === 'Escape') { setNameDraft(person.name); setEditingName(false) } }}
              style={{ fontSize: 13, fontWeight: 600, border: 'none', borderBottom: '1px solid #185FA5', outline: 'none', background: 'transparent', width: '100%', padding: '0 2px' }}
            />
          ) : (
            <p onClick={() => setEditingName(true)} title="Click to edit name" style={{ margin: 0, fontSize: 13, fontWeight: 600, cursor: 'text' }}>{person.name}</p>
          )}
          {editingRole ? (
            <input
              autoFocus
              value={roleDraft}
              onChange={e => setRoleDraft(e.target.value)}
              onBlur={saveRole}
              onKeyDown={e => { if (e.key === 'Enter') saveRole(); if (e.key === 'Escape') { setRoleDraft(person.role || ''); setEditingRole(false) } }}
              placeholder="Add role..."
              style={{ fontSize: 11, border: 'none', borderBottom: '1px solid #ccc', outline: 'none', background: 'transparent', width: '100%', marginTop: 2, color: '#666', padding: '0 2px' }}
            />
          ) : (
            <p onClick={() => setEditingRole(true)} title="Click to edit role" style={{ margin: '2px 0 0', fontSize: 11, color: '#888', cursor: 'text' }}>{person.role || <span style={{ color: '#ccc' }}>Click to add role</span>}</p>
          )}
        </div>
        <button onClick={() => onDelete(person.id)} title="Remove person" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ccc', fontSize: 15, padding: '0 2px', flexShrink: 0, lineHeight: 1 }}>✕</button>
      </div>

      {/* Tasks */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {openTasks.length === 0
          ? <p style={{ fontSize: 11, color: '#bbb', margin: 0 }}>No open tasks</p>
          : openTasks.map(task => (
            <div key={task.id} style={{ fontSize: 12, padding: '5px 8px', borderRadius: 6, background: '#fafafa', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
              <span style={{ color: PRIORITY_COLOR[task.priority] || '#ccc', flexShrink: 0, marginTop: 1 }}>•</span>
              <span style={{ color: '#333', lineHeight: 1.4 }}>{task.title}</span>
            </div>
          ))
        }
      </div>

      {/* Add task */}
      {showAddTask ? (
        <div style={{ display: 'flex', gap: 4, marginTop: 10 }}>
          <input
            autoFocus
            value={taskDraft}
            onChange={e => setTaskDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') submitTask(); if (e.key === 'Escape') { setShowAddTask(false); setTaskDraft('') } }}
            placeholder="Task title..."
            style={{ flex: 1, fontSize: 12, padding: '5px 8px', border: '1px solid #185FA5', borderRadius: 6, outline: 'none' }}
          />
          <button onClick={submitTask} style={{ fontSize: 11, padding: '5px 9px', borderRadius: 6, border: 'none', background: '#185FA5', color: 'white', cursor: 'pointer', fontWeight: 600 }}>Add</button>
          <button onClick={() => { setShowAddTask(false); setTaskDraft('') }} style={{ fontSize: 11, padding: '5px 8px', borderRadius: 6, border: 'none', background: '#eee', color: '#666', cursor: 'pointer' }}>✕</button>
        </div>
      ) : (
        <button onClick={() => setShowAddTask(true)} style={{ marginTop: 10, fontSize: 11, padding: '4px 10px', borderRadius: 7, border: '1px dashed #185FA5', background: 'transparent', color: '#185FA5', cursor: 'pointer', fontWeight: 500 }}>+ Add task</button>
      )}
    </div>
  )
}

// ---------- Bucket board ----------
function BucketBoard({ bucket, bTasks, students, onDone, onDelete, onUpdateDue, onUpdateTitle, onUpdateStudent, newStudentName, setNewStudentName, addingStudent, onAddStudent, customLabel, onSaveLabel, onAddManualTask, onDeleteBucket, people, taskAssignees, onUpdateAssignee }) {
  const placement = GRID_PLACEMENT[bucket.id] || {}
  const [editingLabel, setEditingLabel] = useState(false)
  const [labelDraft, setLabelDraft] = useState(customLabel || bucket.label)
  const [showAddManual, setShowAddManual] = useState(false)
  const [manualTitle, setManualTitle] = useState('')

  function saveLabel() {
    setEditingLabel(false)
    const val = labelDraft.trim() || bucket.label
    setLabelDraft(val)
    onSaveLabel(bucket.id, val)
  }

  function confirmManual() {
    if (!manualTitle.trim()) return
    onAddManualTask(bucket.id, manualTitle.trim())
    setManualTitle('')
    setShowAddManual(false)
  }

  function cancelManual() {
    setManualTitle('')
    setShowAddManual(false)
  }

  return (
    <div style={{ ...card, gridColumn: placement.column, gridRow: placement.row, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '9px 12px', background: bucket.bg, borderBottom: `1px solid ${bucket.color}33`, display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        {editingLabel ? (
          <input
            autoFocus
            value={labelDraft}
            onChange={e => setLabelDraft(e.target.value)}
            onBlur={saveLabel}
            onKeyDown={e => { if (e.key === 'Enter') saveLabel(); if (e.key === 'Escape') { setLabelDraft(customLabel || bucket.label); setEditingLabel(false) } }}
            style={{ flex: 1, fontSize: 12.5, fontWeight: 700, border: 'none', borderBottom: `1px solid ${bucket.color}`, outline: 'none', background: 'transparent', color: bucket.color, padding: '0 2px' }}
          />
        ) : (
          <span
            onClick={() => setEditingLabel(true)}
            title="Click to rename"
            style={{ fontSize: 12.5, fontWeight: 700, color: bucket.color, flex: 1, cursor: 'text' }}
          >{customLabel || bucket.label}</span>
        )}
        <button
          onClick={() => setShowAddManual(v => !v)}
          title="Add task directly"
          style={{ fontSize: 10, padding: '2px 7px', borderRadius: 8, border: `1px solid ${bucket.color}55`, background: 'transparent', color: bucket.color, cursor: 'pointer', flexShrink: 0, fontWeight: 600 }}
        >+ Add</button>
        <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 20, background: bucket.color + '22', color: bucket.color }}>{bTasks.length}</span>
        <button
          onClick={() => onDeleteBucket(bucket.id)}
          title="Remove bucket"
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, color: '#bbb', padding: '0 2px', flexShrink: 0, lineHeight: 1 }}
        >✕</button>
      </div>

      <div style={{ padding: 8, overflowY: 'auto', flex: 1 }}>
        {showAddManual && (
          <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
            <input
              autoFocus
              value={manualTitle}
              onChange={e => setManualTitle(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') confirmManual(); if (e.key === 'Escape') cancelManual() }}
              placeholder="Task title..."
              style={{ flex: 1, fontSize: 12, padding: '5px 8px', border: `1px solid ${bucket.color}66`, borderRadius: 6, outline: 'none' }}
            />
            <button onClick={confirmManual} style={{ fontSize: 11, padding: '5px 9px', borderRadius: 6, border: 'none', background: bucket.color, color: 'white', cursor: 'pointer', fontWeight: 600 }}>Add</button>
            <button onClick={cancelManual} style={{ fontSize: 11, padding: '5px 8px', borderRadius: 6, border: 'none', background: '#eee', color: '#666', cursor: 'pointer' }}>✕</button>
          </div>
        )}
        {bucket.id === 'ascend_classes' && (
          <div style={{ marginBottom: 8 }}>
            {students.length === 0 ? (
              <p style={{ fontSize: 11, color: '#aaa', padding: '4px 4px' }}>No students yet</p>
            ) : students.map(s => (
              <StudentRow key={s.id} student={s} onUpdate={onUpdateStudent} />
            ))}
            <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
              <input
                value={newStudentName}
                onChange={e => setNewStudentName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') onAddStudent() }}
                placeholder="Add student name..."
                style={{ flex: 1, fontSize: 11, padding: '5px 7px', border: '1px solid #e5e5e5', borderRadius: 6, outline: 'none' }}
              />
              <button onClick={onAddStudent} disabled={addingStudent || !newStudentName.trim()} style={{ fontSize: 11, padding: '5px 9px', borderRadius: 6, border: 'none', background: '#993556', color: 'white', cursor: 'pointer' }}>+</button>
            </div>
          </div>
        )}

        {bTasks.length === 0 ? (
          <p style={{ fontSize: 11, color: '#aaa', textAlign: 'center', padding: '8px 0' }}>Nothing here</p>
        ) : bTasks.map(task => (
          <TaskCard key={task.id} task={task} onDone={onDone} onDelete={onDelete} onUpdateDue={onUpdateDue} onUpdateTitle={onUpdateTitle}
            bucketId={bucket.id} people={people} assignee={taskAssignees?.[task.id]} onUpdateAssignee={onUpdateAssignee} />
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const [tasks, setTasks] = useState([])
  const [students, setStudents] = useState([])
  const [people, setPeople] = useState([])
  const [brief, setBrief] = useState(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('today') // today | brief | people
  const [newStudentName, setNewStudentName] = useState('')
  const [addingStudent, setAddingStudent] = useState(false)
  const [expandedTask, setExpandedTask] = useState(null) // task object shown in the People-tab modal
  const [isRecording, setIsRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [calendarConnected, setCalendarConnected] = useState(false)
  const [analytics, setAnalytics] = useState(null)
  const [windowWidth, setWindowWidth] = useState(window.innerWidth)
  const [bucketLabels, setBucketLabels] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bucketLabels') || '{}') } catch { return {} }
  })
  const [newPersonName, setNewPersonName] = useState('')
  const [newPersonRole, setNewPersonRole] = useState('')
  const [addingPerson, setAddingPerson] = useState(false)
  const [hiddenBuckets, setHiddenBuckets] = useState(() => {
    try { return new Set(JSON.parse(localStorage.getItem('hiddenBuckets') || '[]')) } catch { return new Set() }
  })
  const [customBuckets, setCustomBuckets] = useState(() => {
    try { return JSON.parse(localStorage.getItem('customBuckets') || '[]') } catch { return [] }
  })
  const [addingBucket, setAddingBucket] = useState(false)
  const [newBucketName, setNewBucketName] = useState('')
  const [taskAssignees, setTaskAssignees] = useState(() => {
    try { return JSON.parse(localStorage.getItem('taskAssignees') || '{}') } catch { return {} }
  })
  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const isMobile = windowWidth < 768

  useEffect(() => {
    const handler = () => setWindowWidth(window.innerWidth)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  async function handleMicClick() {
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunksRef.current = []
      const mr = new MediaRecorder(stream)
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        setIsRecording(false)
        setTranscribing(true)
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          const { text } = await transcribeAudio(blob)
          setInput(text)
        } catch {
          setError('Transcription failed — check backend or mic permissions.')
        } finally {
          setTranscribing(false)
        }
      }
      mediaRecorderRef.current = mr
      setError('')
      setIsRecording(true)
      mr.start()
    } catch {
      setError('Could not access microphone — check browser permissions.')
    }
  }

  const loadAll = useCallback(async () => {
    try {
      const [t, s, b, p, cal, dbBuckets] = await Promise.all([fetchTasks(), fetchStudents(), fetchBrief(), fetchPeople(), fetchCalendarStatus(), fetchCustomBuckets()])
      setTasks(t)
      setStudents(s)
      setBrief(b)
      setPeople(p)
      setCalendarConnected(cal.connected)
      // Merge DB custom buckets with any localStorage color info
      if (dbBuckets.length > 0) {
        const saved = JSON.parse(localStorage.getItem('customBuckets') || '[]')
        const savedById = Object.fromEntries(saved.map(cb => [cb.id, cb]))
        const palette = [
          { color: '#0D7377', bg: '#E0F7FA' }, { color: '#6B4EAD', bg: '#F3E8FF' },
          { color: '#B45309', bg: '#FEF3C7' }, { color: '#065F46', bg: '#D1FAE5' },
          { color: '#6B21A8', bg: '#F5F3FF' },
        ]
        const merged = dbBuckets.map((db, i) => ({
          id: db.id,
          label: db.name,
          color: savedById[db.id]?.color || palette[i % palette.length].color,
          bg: savedById[db.id]?.bg || palette[i % palette.length].bg,
        }))
        setCustomBuckets(merged)
        localStorage.setItem('customBuckets', JSON.stringify(merged))
      }
      // Seed Ishita if she's not in the people list yet
      if (!p.some(person => person.name === 'Ishita')) {
        try {
          const ishita = await createPerson('Ishita', 'Founder')
          setPeople(prev => [ishita, ...prev])
        } catch {}
      }
    } catch (e) {
      setError('Could not load dashboard data. Is the backend running?')
    }
  }, [])

  useEffect(() => {
    if (tab === 'history' && !analytics) {
      fetchAnalytics().then(setAnalytics).catch(() => {})
    }
  }, [tab, analytics])

  // Auto-refresh calendar events every 60s while the brief tab is open.
  // Calls the lightweight /events/today endpoint — no LLM, no Groq cost.
  useEffect(() => {
    if (tab !== 'brief' || !calendarConnected) return
    const interval = setInterval(() => {
      fetch('/api/calendar/events/today')
        .then(r => r.ok ? r.json() : [])
        .then(events => setBrief(prev => prev ? { ...prev, calendar_events: events } : prev))
        .catch(() => {})
    }, 60_000)
    return () => clearInterval(interval)
  }, [tab, calendarConnected])

  useEffect(() => {
    // Handle redirect back from Google OAuth
    const params = new URLSearchParams(window.location.search)
    const calParam = params.get('calendar')
    if (calParam === 'connected') {
      setCalendarConnected(true)
      setTab('brief')
      window.history.replaceState({}, '', '/')
    } else if (calParam === 'error') {
      setError('Google Calendar connection failed — check the backend terminal.')
      window.history.replaceState({}, '', '/')
    }
    loadAll()
  }, [loadAll])

  async function handleAdd() {
    if (!input.trim()) return
    setLoading(true)
    setError('')
    try {
      const task = await createTask(input.trim())
      setTasks(prev => [task, ...prev])
      setInput('')
      // Refresh people in case this task named someone new
      fetchPeople().then(setPeople).catch(() => {})
      // Refresh brief so calendar events from this task appear immediately
      fetchBrief().then(setBrief).catch(() => {})
    } catch (e) {
      setError('Could not classify task. Check the backend terminal for details.')
    } finally {
      setLoading(false)
    }
  }

  async function handleRefreshBrief() {
    try {
      setBrief(await fetchBrief())
    } catch (e) {
      setError('Could not refresh the daily brief — check the backend terminal.')
    }
  }

  async function handleDone(id, done) {
    const updated = await updateTask(id, { done: !done })
    setTasks(prev => prev.map(t => t.id === id ? updated : t))
    // If marking done, reload tasks so any spawned recurring task appears
    if (!done) fetchTasks().then(setTasks).catch(() => {})
  }

  async function handleDelete(id) {
    await deleteTask(id)
    setTasks(prev => prev.filter(t => t.id !== id))
  }

  async function handleUpdateTitle(id, title) {
    try {
      const updated = await updateTask(id, { title })
      setTasks(prev => prev.map(t => t.id === id ? updated : t))
    } catch (e) {
      setError('Could not update task title.')
    }
  }

  async function handleUpdateRecurrence(id, recurrence) {
    try {
      const updated = await updateTask(id, { recurrence })
      setTasks(prev => prev.map(t => t.id === id ? updated : t))
    } catch (e) {
      setError('Could not update recurrence.')
    }
  }

  async function handleUpdateDue(id, due, dueDateIso) {
    try {
      const patch = dueDateIso ? { due, due_date: dueDateIso } : { due }
      const updated = await updateTask(id, patch)
      setTasks(prev => prev.map(t => t.id === id ? updated : t))
    } catch (e) {
      setError('Could not update the deadline.')
    }
  }

  async function handleAddStudent() {
    if (!newStudentName.trim()) return
    setAddingStudent(true)
    try {
      const student = await createStudent({ name: newStudentName.trim() })
      setStudents(prev => [...prev, student].sort((a, b) => a.name.localeCompare(b.name)))
      setNewStudentName('')
    } catch (e) {
      setError('Could not add student.')
    } finally {
      setAddingStudent(false)
    }
  }

  async function handleUpdateStudent(id, patch) {
    try {
      const updated = await updateStudent(id, patch)
      setStudents(prev => prev.map(s => s.id === id ? updated : s))
    } catch (e) {
      setError('Could not update student.')
    }
  }

  function handleSaveBucketLabel(bucketId, label) {
    const updated = { ...bucketLabels, [bucketId]: label }
    setBucketLabels(updated)
    localStorage.setItem('bucketLabels', JSON.stringify(updated))
  }

  async function handleAddManualTask(bucketId, title) {
    try {
      const task = await createManualTask(bucketId, title)
      setTasks(prev => [task, ...prev])
    } catch (e) {
      setError('Could not add task.')
    }
  }

  async function handleAddPersonTask(personId, title) {
    try {
      const task = await createManualTask('udukku', title, personId)
      setTasks(prev => [task, ...prev])
      fetchPeople().then(setPeople).catch(() => {})
    } catch (e) {
      setError('Could not add task.')
    }
  }

  function handleUpdateAssignee(taskId, name) {
    const updated = { ...taskAssignees, [taskId]: name }
    setTaskAssignees(updated)
    localStorage.setItem('taskAssignees', JSON.stringify(updated))
  }

  async function handleUpdatePerson(id, patch) {
    try {
      const updated = await updatePerson(id, patch)
      setPeople(prev => prev.map(p => p.id === id ? { ...p, ...updated } : p))
    } catch (e) {
      setError('Could not update person.')
    }
  }

  async function handleDeleteBucket(bucketId) {
    const label = [...BUCKETS, ...customBuckets].find(b => b.id === bucketId)?.label || bucketId
    if (!window.confirm(`Remove "${label}" bucket? Tasks inside will be kept but unassigned.`)) return
    if (BUCKETS.some(b => b.id === bucketId)) {
      const updated = new Set([...hiddenBuckets, bucketId])
      setHiddenBuckets(updated)
      localStorage.setItem('hiddenBuckets', JSON.stringify([...updated]))
    } else {
      try {
        await deleteBucketFromDB(bucketId)
      } catch {}
      const updated = customBuckets.filter(b => b.id !== bucketId)
      setCustomBuckets(updated)
      localStorage.setItem('customBuckets', JSON.stringify(updated))
    }
  }

  async function handleAddBucket() {
    if (!newBucketName.trim()) return
    const palette = [
      { color: '#0D7377', bg: '#E0F7FA' }, { color: '#6B4EAD', bg: '#F3E8FF' },
      { color: '#B45309', bg: '#FEF3C7' }, { color: '#065F46', bg: '#D1FAE5' },
      { color: '#6B21A8', bg: '#F5F3FF' },
    ]
    const c = palette[customBuckets.length % palette.length]
    const id = `custom_${Date.now()}`
    const newBucket = { id, label: newBucketName.trim(), ...c }
    try {
      await createBucketInDB(id, newBucketName.trim())
    } catch (e) {
      setError('Could not create bucket.')
      return
    }
    const updated = [...customBuckets, newBucket]
    setCustomBuckets(updated)
    localStorage.setItem('customBuckets', JSON.stringify(updated))
    setNewBucketName('')
    setAddingBucket(false)
  }

  async function handleAddPerson() {
    if (!newPersonName.trim()) return
    setAddingPerson(true)
    try {
      const person = await createPerson(newPersonName.trim(), newPersonRole.trim())
      setPeople(prev => [...prev, person])
      setNewPersonName('')
      setNewPersonRole('')
    } catch (e) {
      setError('Could not add person.')
    } finally {
      setAddingPerson(false)
    }
  }

  async function handleDeletePerson(id) {
    const person = people.find(p => p.id === id)
    if (!window.confirm(`Remove ${person?.name || 'this person'} from the People tab? Their tasks will be kept.`)) return
    try {
      await deletePerson(id)
      setPeople(prev => prev.filter(p => p.id !== id))
    } catch (e) {
      setError('Could not remove person.')
    }
  }

  const PRIORITY_RANK = { high: 0, medium: 1, low: 2 }
  const openTasksByBucket = (bucketId) => tasks
    .filter(t => t.bucket_id === bucketId && !t.done)
    .sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority])

  const boardProps = {
    students, onDone: handleDone, onDelete: handleDelete, onUpdateDue: handleUpdateDue,
    onUpdateTitle: handleUpdateTitle,
    onUpdateStudent: handleUpdateStudent,
    newStudentName, setNewStudentName, addingStudent, onAddStudent: handleAddStudent,
    onSaveLabel: handleSaveBucketLabel, customLabel: undefined,
    onAddManualTask: handleAddManualTask,
    onDeleteBucket: handleDeleteBucket,
    people, taskAssignees, onUpdateAssignee: handleUpdateAssignee,
  }

  return (
    <div style={{ maxWidth: 1440, margin: '0 auto', padding: isMobile ? '16px 12px 80px' : '24px 24px', fontFamily: 'system-ui, sans-serif', color: '#222' }}>
      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        * { box-sizing: border-box; }
        html { zoom: 1.10; }
      `}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: isMobile ? 16 : 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#E6F1FB', color: '#185FA5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 13 }}>IS</div>
          <div>
            <p style={{ margin: 0, fontSize: isMobile ? 14 : 16, fontWeight: 600 }}>Ishita HQ</p>
            <p style={{ margin: 0, fontSize: 11, color: '#777' }}>{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}</p>
          </div>
        </div>
        {/* Desktop tabs — hidden on mobile (shown as bottom nav instead) */}
        {!isMobile && (
          <div style={{ display: 'flex', gap: 6 }}>
            {[['today', 'My Tasks'], ['brief', "Today's Brief"], ['people', 'People'], ['history', 'History']].map(([id, label]) => (
              <button key={id} onClick={() => setTab(id)} style={{ padding: '5px 14px', fontSize: 13, borderRadius: 20, border: '0.5px solid', borderColor: tab === id ? '#185FA5' : '#ddd', background: tab === id ? '#E6F1FB' : 'white', color: tab === id ? '#185FA5' : '#555', cursor: 'pointer', fontWeight: tab === id ? 600 : 400 }}>{label}</button>
            ))}
          </div>
        )}
      </div>

      {/* Mobile bottom nav */}
      {isMobile && (
        <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'white', borderTop: '1px solid #e5e5e5', display: 'flex', zIndex: 100, paddingBottom: 'env(safe-area-inset-bottom)' }}>
          {[['today', '🗂', 'My Tasks'], ['brief', '💡', "Today's Brief"], ['people', '👥', 'People'], ['history', '📈', 'History']].map(([id, icon, label]) => (
            <button key={id} onClick={() => setTab(id)} style={{ flex: 1, padding: '10px 4px 8px', border: 'none', background: 'none', cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              <span style={{ fontSize: 10, color: tab === id ? '#185FA5' : '#999', fontWeight: tab === id ? 600 : 400 }}>{label}</span>
            </button>
          ))}
        </div>
      )}

      {error && <p style={{ color: '#E24B4A', fontSize: 13, marginBottom: 18 }}>{error}</p>}

      {/* ---------- Today: capture bar centered, 7 buckets around it ---------- */}
      {tab === 'today' && (
        isMobile ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Capture bar — pinned at top on mobile */}
            <div style={{ ...card, border: '1px solid #185FA5', padding: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 16 }}>✨</span>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleAdd() }}
                placeholder={isRecording ? 'Listening…' : 'Drop a task, a thought...'}
                style={{ flex: 1, border: 'none', outline: 'none', fontSize: 13 }}
              />
              <button onClick={handleMicClick} disabled={transcribing} style={{ flexShrink: 0, width: 28, height: 28, borderRadius: '50%', border: 'none', cursor: transcribing ? 'default' : 'pointer', background: isRecording ? '#E24B4A' : transcribing ? '#185FA5' : '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: isRecording ? 'pulse 1.2s infinite' : 'none' }}>{transcribing ? <span style={{ fontSize: 10, color: 'white' }}>…</span> : <MicIcon color={isRecording ? 'white' : '#666'} />}</button>
              <button onClick={handleAdd} disabled={loading || !input.trim()} style={{ flexShrink: 0, padding: '6px 12px', fontSize: 12, borderRadius: 8, border: 'none', background: loading ? '#aaa' : '#185FA5', color: 'white', cursor: loading ? 'default' : 'pointer' }}>{loading ? '…' : 'Send'}</button>
            </div>
            {BUCKETS.map(b => (
              <BucketBoard key={b.id} bucket={b} bTasks={openTasksByBucket(b.id)} {...boardProps} customLabel={bucketLabels[b.id]} />
            ))}
          </div>
        ) : (
          <div style={{ zoom: 0.95 }}>
            {/* Capture bar — full width at top */}
            <div style={{ ...card, border: '1.5px solid #185FA5', padding: '10px 14px', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 18, flexShrink: 0 }}>✨</span>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleAdd() }}
                placeholder={isRecording ? 'Listening…' : transcribing ? 'Transcribing…' : 'Drop a task, a thought, anything...'}
                style={{ flex: 1, border: 'none', outline: 'none', fontSize: 13, background: 'transparent' }}
              />
              <button onClick={handleMicClick} disabled={transcribing} title={isRecording ? 'Stop' : transcribing ? 'Transcribing…' : 'Speak a task'} style={{ flexShrink: 0, width: 28, height: 28, borderRadius: '50%', border: 'none', cursor: transcribing ? 'default' : 'pointer', background: isRecording ? '#E24B4A' : transcribing ? '#185FA5' : '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: isRecording ? 'pulse 1.2s infinite' : 'none' }}>{transcribing ? <span style={{ fontSize: 10, color: 'white' }}>…</span> : <MicIcon size={13} color={isRecording ? 'white' : '#666'} />}</button>
              <button onClick={handleAdd} disabled={loading || !input.trim()} style={{ flexShrink: 0, padding: '7px 18px', fontSize: 13, borderRadius: 8, border: 'none', background: loading ? '#aaa' : '#185FA5', color: 'white', cursor: loading ? 'default' : 'pointer', fontWeight: 600 }}>{loading ? 'Classifying…' : 'Send'}</button>
              <div style={{ width: 1, height: 24, background: '#e5e5e5', flexShrink: 0 }} />
              {addingBucket ? (
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                  <input autoFocus value={newBucketName} onChange={e => setNewBucketName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddBucket(); if (e.key === 'Escape') setAddingBucket(false) }} placeholder="Bucket name..." style={{ fontSize: 12, padding: '5px 9px', border: '1px solid #185FA5', borderRadius: 7, outline: 'none', width: 140 }} />
                  <button onClick={handleAddBucket} style={{ fontSize: 12, padding: '5px 11px', borderRadius: 7, border: 'none', background: '#185FA5', color: 'white', cursor: 'pointer', fontWeight: 600 }}>Add</button>
                  <button onClick={() => { setAddingBucket(false); setNewBucketName('') }} style={{ fontSize: 12, padding: '5px 8px', borderRadius: 7, border: 'none', background: '#eee', color: '#666', cursor: 'pointer' }}>✕</button>
                </div>
              ) : (
                <button onClick={() => setAddingBucket(true)} style={{ flexShrink: 0, fontSize: 12, padding: '6px 13px', borderRadius: 7, border: '1px dashed #185FA5', background: 'transparent', color: '#185FA5', cursor: 'pointer', whiteSpace: 'nowrap', fontWeight: 500 }}>+ New Bucket</button>
              )}
            </div>

            {/* Bucket grid — Udukku tall on left, others auto-flow to fill vacant slots */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr 1fr', gridAutoRows: 'minmax(130px, calc((100vh - 310px) / 3))', gridAutoFlow: 'row dense', gap: 12 }}>
              {BUCKETS.filter(b => !hiddenBuckets.has(b.id)).map(b => (
                <BucketBoard key={b.id} bucket={b} bTasks={openTasksByBucket(b.id)} {...boardProps} customLabel={bucketLabels[b.id]} />
              ))}
              {customBuckets.map(cb => (
                <BucketBoard key={cb.id} bucket={cb} bTasks={openTasksByBucket(cb.id)} {...boardProps} customLabel={bucketLabels[cb.id]} />
              ))}
            </div>
          </div>
        )
      )}

      {/* ---------- Daily brief ---------- */}
      {tab === 'brief' && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.3fr 1fr', gap: 16, alignItems: 'start' }}>
          <div style={{ ...card, padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <p style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>💡 What matters today</p>
              <button onClick={handleRefreshBrief} style={{ fontSize: 11, padding: '3px 9px', borderRadius: 6, border: '1px solid #ddd', background: 'white', color: '#666', cursor: 'pointer' }}>Refresh</button>
            </div>
            {!brief ? <p style={{ fontSize: 12, color: '#999' }}>Loading…</p> : brief.what_matters_today.length === 0 ? (
              <p style={{ fontSize: 12, color: '#999' }}>Nothing urgent right now.</p>
            ) : (() => {
              const ALL_BUCKETS = [...BUCKETS, ...([{ id: 'udukku', label: 'Udukku' }])]
              const BUCKET_LABEL_MAP = Object.fromEntries([...BUCKETS].map(b => [b.id, b.label]))
              return brief.what_matters_today.map((item, i) => {
                const matchedTask = tasks.find(t => !t.done && (t.title === item.text || (item.text && item.text.includes(t.title))))
                const bucketLabel = matchedTask ? (BUCKET_LABEL_MAP[matchedTask.bucket_id] || matchedTask.bucket_id) : null
                return (
                  <p key={i} style={{ fontSize: 12.5, lineHeight: 1.6, margin: '0 0 9px', display: 'flex', gap: 7, alignItems: 'flex-start' }}>
                    <span style={{ color: PRIORITY_COLOR[item.priority] || '#999', fontSize: 16, lineHeight: 1.2, flexShrink: 0 }}>•</span>
                    <span>
                      {bucketLabel && <span style={{ fontSize: 10.5, fontWeight: 700, color: '#185FA5', background: '#E6F1FB', padding: '1px 6px', borderRadius: 8, marginRight: 6, whiteSpace: 'nowrap' }}>{bucketLabel}</span>}
                      {item.text}
                    </span>
                  </p>
                )
              })
            })()}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Calendar card */}
            <div style={{ ...card, padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>📅 Today's calendar</p>
                {calendarConnected ? (
                  <button
                    onClick={async () => { await disconnectCalendar(); setCalendarConnected(false) }}
                    style={{ fontSize: 11, padding: '3px 10px', borderRadius: 6, border: '1px solid #eee', background: 'white', color: '#bbb', cursor: 'pointer' }}
                  >Disconnect</button>
                ) : (
                  <button
                    onClick={openCalendarAuth}
                    style={{ fontSize: 11, padding: '3px 10px', borderRadius: 6, border: 'none', background: '#185FA5', color: 'white', cursor: 'pointer' }}
                  >Connect Google Calendar</button>
                )}
              </div>
              {!calendarConnected ? (
                <p style={{ fontSize: 12, color: '#999' }}>Connect Google Calendar to see today's events here and get conflict-aware planning in your brief.</p>
              ) : !brief || !brief.calendar_events || brief.calendar_events.length === 0 ? (
                <p style={{ fontSize: 12, color: '#999' }}>No events scheduled for today.</p>
              ) : brief.calendar_events.map((ev, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '6px 0', borderBottom: i < brief.calendar_events.length - 1 ? '1px solid #f0f0f0' : 'none' }}>
                  <div style={{ flexShrink: 0, width: 3, alignSelf: 'stretch', borderRadius: 2, background: '#185FA5', marginTop: 2 }} />
                  <div>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 600 }}>{ev.title}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#888' }}>
                      {ev.all_day ? 'All day' : `${ev.start} – ${ev.end}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ ...card, padding: '14px 16px' }}>
              <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 600 }}>👥 Who to check on today</p>
              {!brief || brief.who_to_check_on.length === 0 ? (
                <p style={{ fontSize: 12, color: '#999' }}>No follow-ups pending.</p>
              ) : brief.who_to_check_on.map((f, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '6px 0', borderBottom: i < brief.who_to_check_on.length - 1 ? '1px solid #f0f0f0' : 'none' }}>
                  <div style={{ width: 22, height: 22, borderRadius: '50%', background: '#f0f0f0', fontSize: 10, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{f.name[0]}</div>
                  <div>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 600 }}>{f.name}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#888' }}>{f.reason}</p>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ ...card, padding: '14px 16px' }}>
              <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 600 }}>🕓 Recent days</p>
              {!brief || brief.recent_days.length === 0 ? (
                <p style={{ fontSize: 12, color: '#999' }}>History will appear here from tomorrow.</p>
              ) : brief.recent_days.map((d, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0' }}>
                  <span>{new Date(d.report_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                  <span style={{ color: '#888' }}>{d.tasks_completed} done · {d.tasks_carried_over} carried over</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ---------- People ---------- */}
      {tab === 'people' && (
        <div>
          {/* Add person form */}
          <div style={{ ...card, padding: '12px 16px', marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#555', marginRight: 4 }}>+ Add person</span>
            <input
              value={newPersonName}
              onChange={e => setNewPersonName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleAddPerson() }}
              placeholder="Name"
              style={{ fontSize: 12, padding: '5px 9px', border: '1px solid #e5e5e5', borderRadius: 7, outline: 'none', width: 140 }}
            />
            <input
              value={newPersonRole}
              onChange={e => setNewPersonRole(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleAddPerson() }}
              placeholder="Role (optional)"
              style={{ fontSize: 12, padding: '5px 9px', border: '1px solid #e5e5e5', borderRadius: 7, outline: 'none', width: 160 }}
            />
            <button onClick={handleAddPerson} disabled={addingPerson || !newPersonName.trim()} style={{ fontSize: 12, padding: '5px 14px', borderRadius: 7, border: 'none', background: '#185FA5', color: 'white', cursor: 'pointer', fontWeight: 600 }}>Add</button>
          </div>

          {people.length === 0 ? (
            <p style={{ fontSize: 13, color: '#999' }}>Loading team…</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
              {people.map(person => (
                <PersonCard
                  key={person.id}
                  person={person}
                  onDelete={handleDeletePerson}
                  onUpdatePerson={handleUpdatePerson}
                  onAddTask={handleAddPersonTask}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ---------- History & Analytics ---------- */}
      {tab === 'history' && (() => {
        if (!analytics) return <p style={{ fontSize: 13, color: '#999' }}>Loading…</p>

        const BUCKET_LABELS = {
          udukku: 'Udukku', ascend_social: 'Ascend Social', ascend_classes: 'Classes',
          music: 'Music', social_brand: 'My Social', fitness: 'Fitness', personal: 'Personal',
        }
        const BUCKET_COLORS = {
          udukku: '#185FA5', ascend_social: '#3B6D11', ascend_classes: '#993556',
          music: '#534AB7', social_brand: '#854F0B', fitness: '#993C1D', personal: '#555555',
        }
        const PRIORITY_COLORS = { high: '#E24B4A', medium: '#EF9F27', low: '#639922' }

        const dailyData = [...analytics.daily].reverse().map(d => ({
          date: new Date(d.report_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
          Completed: d.tasks_completed,
          'Carried over': d.tasks_carried_over,
        }))

        const bucketData = analytics.by_bucket.map(b => ({
          name: BUCKET_LABELS[b.bucket_id] || b.bucket_id,
          Total: b.total,
          Done: b.done,
          Open: b.open,
          color: BUCKET_COLORS[b.bucket_id] || '#999',
        }))

        const priorityData = analytics.by_priority.map(p => ({
          name: p.priority.charAt(0).toUpperCase() + p.priority.slice(1),
          value: p.count,
          color: PRIORITY_COLORS[p.priority] || '#999',
        }))

        const { this_week, last_week } = analytics.weekly_completions
        const weekDiff = this_week - last_week

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, zoom: 0.95 }}>

            {/* KPI row */}
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', gap: 12 }}>
              {[
                { label: 'Completed this week', value: this_week, sub: last_week === 0 ? 'no data last week' : `${weekDiff >= 0 ? '+' : ''}${weekDiff} vs last week`, color: weekDiff >= 0 ? '#3B6D11' : '#E24B4A' },
                { label: 'Open tasks', value: analytics.by_bucket.reduce((s, b) => s + b.open, 0), sub: 'across all buckets', color: '#185FA5' },
                { label: 'Total tasks ever', value: analytics.by_bucket.reduce((s, b) => s + b.total, 0), sub: `${analytics.by_bucket.reduce((s, b) => s + b.done, 0)} completed`, color: '#555' },
              ].map((kpi, i) => (
                <div key={i} style={{ ...card, padding: '16px 18px' }}>
                  <p style={{ margin: '0 0 4px', fontSize: 12, color: '#888', fontWeight: 500 }}>{kpi.label}</p>
                  <p style={{ margin: '0 0 2px', fontSize: 34, fontWeight: 700, color: '#222' }}>{kpi.value}</p>
                  <p style={{ margin: 0, fontSize: 12, color: kpi.color, fontWeight: 500 }}>{kpi.sub}</p>
                </div>
              ))}
            </div>

            {/* Overdue nudges */}
            {analytics.overdue_nudges?.length > 0 && (
              <div style={{ background: '#fff5f5', border: '1px solid #fcc', borderRadius: 12, padding: '14px 16px' }}>
                <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 600, color: '#E24B4A' }}>⚠️ Needs attention — overdue 3+ days</p>
                {analytics.overdue_nudges.map((n, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: i < analytics.overdue_nudges.length - 1 ? '1px solid #fdd' : 'none' }}>
                    <span style={{ fontWeight: 600 }}>{n.title}</span>
                    <span style={{ color: '#E24B4A' }}>{n.days_open} days overdue · {BUCKET_LABELS[n.bucket_id] || n.bucket_id}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Daily completions bar chart */}
            <div style={{ ...card, padding: '16px 18px' }}>
              <p style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 700 }}>📈 Daily activity (last 30 days)</p>
              {dailyData.length === 0 ? (
                <p style={{ fontSize: 12, color: '#999' }}>No history yet — data appears from the second day onward.</p>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={dailyData} barSize={14} barGap={2}>
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 10 }} allowDecimals={false} width={24} />
                    <Tooltip contentStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Completed" fill="#3B6D11" radius={[3,3,0,0]} />
                    <Bar dataKey="Carried over" fill="#e5e5e5" radius={[3,3,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.4fr 1fr', gap: 16 }}>
              {/* Bucket breakdown */}
              <div style={{ ...card, padding: '16px 18px' }}>
                <p style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 700 }}>🗂 Tasks by bucket</p>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={bucketData} layout="vertical" barSize={14} barGap={2}>
                    <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
                    <Tooltip contentStyle={{ fontSize: 13 }} />
                    <Bar dataKey="Done" stackId="a" radius={[0,0,0,0]}>
                      {bucketData.map((b, i) => <Cell key={i} fill={b.color} />)}
                    </Bar>
                    <Bar dataKey="Open" stackId="a" fill="#e5e5e5" radius={[0,4,4,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Priority breakdown of open tasks */}
              <div style={{ ...card, padding: '16px 18px' }}>
                <p style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 700 }}>🎯 Open tasks by priority</p>
                {priorityData.length === 0 ? (
                  <p style={{ fontSize: 13, color: '#999' }}>No open tasks.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={priorityData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%" cy="50%"
                        outerRadius={95}
                        innerRadius={40}
                        label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                        labelLine={true}
                        fontSize={12}
                      >
                        {priorityData.map((p, i) => <Cell key={i} fill={p.color} />)}
                      </Pie>
                      <Tooltip contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 13 }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>
        )
      })()}

      {/* Click-to-expand: full original task text behind a short summary */}
      {expandedTask && (
        <div onClick={() => setExpandedTask(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div onClick={e => e.stopPropagation()} style={{ ...card, maxWidth: 440, width: '90%', padding: '18px 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>{expandedTask.title}</p>
              <button onClick={() => setExpandedTask(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#999' }}>✕</button>
            </div>
            <p style={{ margin: '0 0 12px', fontSize: 13, lineHeight: 1.6, color: '#444' }}>{expandedTask.raw_text}</p>
            <div style={{ display: 'flex', gap: 8, fontSize: 11, color: '#888' }}>
              <span style={{ color: PRIORITY_COLOR[expandedTask.priority] }}>● {expandedTask.priority}</span>
              <span>{expandedTask.due}</span>
              <span>{expandedTask.done ? 'done' : 'open'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
