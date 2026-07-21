const BASE = '/api'

// ---------- Tasks ----------

export async function fetchTasks() {
  const r = await fetch(`${BASE}/tasks/`)
  if (!r.ok) throw new Error('Failed to load tasks')
  return r.json()
}

export async function createTask(rawText) {
  const r = await fetch(`${BASE}/tasks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: rawText }),
  })
  if (!r.ok) {
    const detail = await r.text()
    throw new Error(detail || 'Failed to create task')
  }
  return r.json()
}

export async function updateTask(id, patch) {
  const r = await fetch(`${BASE}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!r.ok) throw new Error('Failed to update task')
  return r.json()
}

export async function deleteTask(id) {
  const r = await fetch(`${BASE}/tasks/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Failed to delete task')
}

// ---------- Students ----------

export async function fetchStudents() {
  const r = await fetch(`${BASE}/students/`)
  if (!r.ok) throw new Error('Failed to load students')
  return r.json()
}

export async function createStudent(payload) {
  const r = await fetch(`${BASE}/students/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!r.ok) throw new Error('Failed to create student')
  return r.json()
}

export async function updateStudent(id, patch) {
  const r = await fetch(`${BASE}/students/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!r.ok) throw new Error('Failed to update student')
  return r.json()
}

// ---------- Daily brief ----------

export async function fetchBrief() {
  const r = await fetch(`${BASE}/brief/`)
  if (!r.ok) throw new Error('Failed to load daily brief')
  return r.json()
}

// ---------- People ----------

export async function fetchPeople() {
  const r = await fetch(`${BASE}/people/`)
  if (!r.ok) throw new Error('Failed to load people')
  return r.json()
}

// ---------- Calendar ----------

export async function fetchCalendarStatus() {
  const r = await fetch(`${BASE}/calendar/status`)
  if (!r.ok) return { connected: false }
  return r.json()
}

export function openCalendarAuth() {
  window.location.href = '/api/calendar/authorize'
}

export async function disconnectCalendar() {
  const r = await fetch('/api/calendar/disconnect', { method: 'DELETE' })
  if (!r.ok) throw new Error('Failed to disconnect calendar')
}

// ---------- Analytics ----------

export async function fetchAnalytics() {
  const r = await fetch(`${BASE}/analytics/`)
  if (!r.ok) throw new Error('Failed to load analytics')
  return r.json()
}
