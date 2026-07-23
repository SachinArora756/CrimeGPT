import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft, Save, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'
import { INDIA_STATES_DISTRICTS, getDistrictsForState } from '../../data/indiaGeo'

const GENDER_OPTIONS = ['male', 'female', 'other']
const DANGER_LEVELS = ['low', 'medium', 'high', 'critical']
const WANTED_STATUS = ['not_wanted', 'wanted', 'most_wanted', 'surrendered', 'arrested']

interface FromCaseState {
  fromCase?: {
    full_name?: string
    case_fir?: string
    offense_type?: string | null
    station_id?: string | null
    description?: string
  }
}

export default function AddCriminalPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const prefill = (location.state as FromCaseState)?.fromCase
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    full_name: prefill?.full_name || '',
    father_name: '',
    date_of_birth: '',
    gender: 'male',
    nationality: 'Indian',
    occupation: '',
    height_cm: '',
    weight_kg: '',
    build: '',
    complexion: '',
    hair_color: '',
    eye_color: '',
    identifying_marks: '',
    gang_name: '',
    gang_role: '',
    crime_categories: prefill?.offense_type || '',
    modus_operandi: '',
    wanted_status: 'not_wanted',
    danger_level: 'low',
    notes: prefill?.case_fir ? `Linked to FIR: ${prefill.case_fir}` : '',
    station_id: prefill?.station_id || '',
    last_known_state: '',
    last_known_district: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.full_name.trim()) {
      toast.error('Full name is required')
      return
    }
    if (!form.last_known_state) {
      toast.error('State is required')
      return
    }
    if (!form.last_known_district) {
      toast.error('District is required')
      return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        full_name: form.full_name.trim(),
        gender: form.gender,
        nationality: form.nationality || 'Indian',
        wanted_status: form.wanted_status,
        danger_level: form.danger_level,
        total_arrests: 0,
        total_convictions: 0,
        total_firs: 0,
        last_known_state: form.last_known_state,
        last_known_district: form.last_known_district,
      }
      if (form.father_name) payload.father_name = form.father_name
      if (form.date_of_birth) payload.date_of_birth = form.date_of_birth
      if (form.occupation) payload.occupation = form.occupation
      if (form.height_cm) payload.height_cm = parseFloat(form.height_cm)
      if (form.weight_kg) payload.weight_kg = parseFloat(form.weight_kg)
      if (form.build) payload.build = form.build
      if (form.complexion) payload.complexion = form.complexion
      if (form.hair_color) payload.hair_color = form.hair_color
      if (form.eye_color) payload.eye_color = form.eye_color
      if (form.identifying_marks) payload.identifying_marks = form.identifying_marks.split(',').map(s => s.trim()).filter(Boolean)
      if (form.gang_name) payload.gang_name = form.gang_name
      if (form.gang_role) payload.gang_role = form.gang_role
      if (form.crime_categories) payload.crime_categories = form.crime_categories.split(',').map(s => s.trim()).filter(Boolean)
      if (form.modus_operandi) payload.modus_operandi = form.modus_operandi
      if (form.notes) payload.notes = form.notes
      if (form.station_id) payload.station_id = form.station_id

      const res = await api.post('/api/criminal-intelligence/', payload)
      toast.success('Criminal profile created')
      navigate(`/criminal-intel/profiles/${res.data.criminal_id}`)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Failed to create profile')
    } finally {
      setSaving(false)
    }
  }

  const inputClass = "w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white placeholder-dark-500 focus:border-purple-500 focus:outline-none"
  const labelClass = "block text-xs font-medium text-dark-300 mb-1"

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-white">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h1 className="text-2xl font-bold text-white">Add Criminal Profile</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Personal Info */}
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-purple-400 mb-4">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Full Name *</label>
              <input name="full_name" value={form.full_name} onChange={handleChange} className={inputClass} placeholder="Enter full name" required />
            </div>
            <div>
              <label className={labelClass}>Father's Name</label>
              <input name="father_name" value={form.father_name} onChange={handleChange} className={inputClass} placeholder="Father's name" />
            </div>
            <div>
              <label className={labelClass}>Date of Birth</label>
              <input name="date_of_birth" type="date" value={form.date_of_birth} onChange={handleChange} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Gender</label>
              <select name="gender" value={form.gender} onChange={handleChange} className={inputClass}>
                {GENDER_OPTIONS.map(g => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Nationality</label>
              <input name="nationality" value={form.nationality} onChange={handleChange} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Occupation</label>
              <input name="occupation" value={form.occupation} onChange={handleChange} className={inputClass} placeholder="Occupation" />
            </div>
          </div>
        </div>

        {/* Physical Description */}
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-400 mb-4">Physical Description</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className={labelClass}>Height (cm)</label>
              <input name="height_cm" type="number" value={form.height_cm} onChange={handleChange} className={inputClass} placeholder="170" />
            </div>
            <div>
              <label className={labelClass}>Weight (kg)</label>
              <input name="weight_kg" type="number" value={form.weight_kg} onChange={handleChange} className={inputClass} placeholder="70" />
            </div>
            <div>
              <label className={labelClass}>Build</label>
              <input name="build" value={form.build} onChange={handleChange} className={inputClass} placeholder="Medium" />
            </div>
            <div>
              <label className={labelClass}>Complexion</label>
              <input name="complexion" value={form.complexion} onChange={handleChange} className={inputClass} placeholder="Fair/Dark/Wheatish" />
            </div>
            <div>
              <label className={labelClass}>Hair Color</label>
              <input name="hair_color" value={form.hair_color} onChange={handleChange} className={inputClass} placeholder="Black" />
            </div>
            <div>
              <label className={labelClass}>Eye Color</label>
              <input name="eye_color" value={form.eye_color} onChange={handleChange} className={inputClass} placeholder="Brown" />
            </div>
          </div>
          <div className="mt-4">
            <label className={labelClass}>Identifying Marks (comma-separated)</label>
            <input name="identifying_marks" value={form.identifying_marks} onChange={handleChange} className={inputClass} placeholder="Scar on left cheek, tattoo on right arm" />
          </div>
        </div>

        {/* Location */}
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-emerald-400 mb-4">Last Known Location *</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>State *</label>
              <select name="last_known_state" value={form.last_known_state} onChange={(e) => { setForm(prev => ({ ...prev, last_known_state: e.target.value, last_known_district: '' })) }} className={inputClass} required>
                <option value="">Select State</option>
                {INDIA_STATES_DISTRICTS.map(s => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>District *</label>
              <select name="last_known_district" value={form.last_known_district} onChange={handleChange} className={inputClass} disabled={!form.last_known_state} required>
                <option value="">Select District</option>
                {form.last_known_state && getDistrictsForState(form.last_known_state).map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Criminal Info */}
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-red-400 mb-4">Criminal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Gang Name</label>
              <input name="gang_name" value={form.gang_name} onChange={handleChange} className={inputClass} placeholder="Gang affiliation" />
            </div>
            <div>
              <label className={labelClass}>Gang Role</label>
              <input name="gang_role" value={form.gang_role} onChange={handleChange} className={inputClass} placeholder="Leader / Member / Associate" />
            </div>
            <div>
              <label className={labelClass}>Crime Categories (comma-separated)</label>
              <input name="crime_categories" value={form.crime_categories} onChange={handleChange} className={inputClass} placeholder="Robbery, Assault, Drug Trafficking" />
            </div>
            <div>
              <label className={labelClass}>Station ID</label>
              <input name="station_id" value={form.station_id} onChange={handleChange} className={inputClass} placeholder="PS-NORTH-01" />
            </div>
            <div>
              <label className={labelClass}>Wanted Status</label>
              <select name="wanted_status" value={form.wanted_status} onChange={handleChange} className={inputClass}>
                {WANTED_STATUS.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Danger Level</label>
              <select name="danger_level" value={form.danger_level} onChange={handleChange} className={inputClass}>
                {DANGER_LEVELS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className={labelClass}>Modus Operandi</label>
            <textarea name="modus_operandi" value={form.modus_operandi} onChange={handleChange} className={inputClass + " h-20 resize-none"} placeholder="Describe known methods of operation" />
          </div>
        </div>

        {/* Notes */}
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-dark-300 mb-4">Additional Notes</h2>
          <textarea name="notes" value={form.notes} onChange={handleChange} className={inputClass + " h-24 resize-none"} placeholder="Any additional information..." />
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 px-6 py-2.5 disabled:opacity-50">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Create Profile'}
          </button>
        </div>
      </form>
    </div>
  )
}
