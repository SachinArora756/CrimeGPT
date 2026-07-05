import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, MapPin, Phone, Car, Users,
  FileText, Clock, Fingerprint, Dna, Globe, Eye,
  User, BadgeAlert, ExternalLink, Image, ChevronDown, ChevronUp,
  Upload, Plus, Loader2, Trash2, Pen, Save, X
} from 'lucide-react'
import api from '../../api/client'
import toast from 'react-hot-toast'

interface CriminalDetail {
  id: number
  criminal_id: string
  full_name: string
  father_name: string | null
  nicknames: string[] | null
  date_of_birth: string | null
  gender: string
  nationality: string
  religion: string | null
  occupation: string | null
  education: string | null
  height_cm: number | null
  weight_kg: number | null
  build: string | null
  complexion: string | null
  hair_color: string | null
  eye_color: string | null
  identifying_marks: string[] | null
  gang_name: string | null
  gang_role: string | null
  crime_categories: string[] | null
  modus_operandi: string | null
  known_weapons: string[] | null
  wanted_status: string
  danger_level: string
  reward_amount: number | null
  total_arrests: number
  total_convictions: number
  total_firs: number
  first_offense_date: string | null
  last_known_activity: string | null
  prison_history: Array<Record<string, string>> | null
  court_cases: Array<Record<string, string>> | null
  bail_status: string | null
  notes: string | null
  face_embeddings_count: number
  fingerprints_count: number
  dna_profiles_count: number
  aliases: Array<{ alias_name: string; context: string | null }>
  addresses: Array<{ address_type: string; address_line: string; city: string | null; state: string | null; is_current: boolean }>
  vehicles: Array<{ vehicle_type: string; make: string | null; model: string | null; color: string | null; registration_number: string | null; is_stolen: boolean }>
  phone_numbers: Array<{ phone_number: string; phone_type: string; is_active: boolean }>
  social_accounts: Array<{ platform: string; username: string | null; is_active: boolean }>
  associates: Array<{ id: number; associate_name: string; relationship_type: string; gang_connection: string | null; associate_criminal_id: number | null; notes: string | null }>
  case_history: Array<{ fir_number: string | null; case_type: string; sections_applied: string[] | null; police_station: string | null; date_of_offense: string | null; case_status: string | null; verdict: string | null; sentence: string | null }>
  timeline: Array<{ event_date: string; event_type: string; title: string; description: string | null; location: string | null }>
  images: Array<{ id: number; image_path: string; image_type: string | null; description: string | null; created_at: string }>
  created_at: string
}


export default function CriminalProfileDetailPage() {
  const { criminalId } = useParams<{ criminalId: string }>()
  const navigate = useNavigate()
  const [criminal, setCriminal] = useState<CriminalDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'cases' | 'associates' | 'timeline' | 'biometrics'>('overview')
  const [expandedBio, setExpandedBio] = useState<'face' | 'fingerprint' | 'dna' | null>(null)
  const [faceData, setFaceData] = useState<Array<{ id: number; image_path: string; model_name: string; embedding_dim: number; embedding: number[] | null; quality_score: number | null; created_at: string | null }>>([])
  const [fpData, setFpData] = useState<Array<{ id: number; finger_type: string; image_path: string | null; template_data: { minutiae_count?: number; descriptors?: number[][]; keypoints?: Array<{ x: number; y: number; size: number; angle: number }> } | null; quality_score: number | null; created_at: string | null }>>([])
  const [dnaData, setDnaData] = useState<Array<{ id: number; dna_id: string; sample_number: string | null; laboratory: string | null; collection_date: string | null; profile_data: Record<string, unknown> | null; loci_markers: Record<string, unknown> | null; created_at: string | null }>>([])
  const [bioLoading, setBioLoading] = useState(false)
  const [uploading, setUploading] = useState<'face' | 'fingerprint' | null>(null)
  const [showDnaForm, setShowDnaForm] = useState(false)
  const [dnaForm, setDnaForm] = useState({ dna_id: '', sample_number: '', laboratory: '', collection_date: '' })
  const faceInputRef = useRef<HTMLInputElement>(null)
  const fpInputRef = useRef<HTMLInputElement>(null)
  const [fpFingerType, setFpFingerType] = useState('right_thumb')
  const [editing, setEditing] = useState(false)
  const [editSaving, setEditSaving] = useState(false)
  const [editForm, setEditForm] = useState({
    full_name: '',
    father_name: '',
    date_of_birth: '',
    gender: 'male',
    nationality: '',
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
    crime_categories: '',
    modus_operandi: '',
    wanted_status: 'not_wanted',
    danger_level: 'low',
    reward_amount: '',
    notes: '',
    station_id: '',
  })

  const handleFaceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !criminalId) return
    setUploading('face')
    try {
      const formData = new FormData()
      formData.append('file', file)
      await api.post(`/api/criminal-intelligence/${criminalId}/biometrics/faces`, formData)
      toast.success('Face embedding generated successfully')
      const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/faces`)
      setFaceData(res.data)
      fetchCriminal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Face upload failed')
    } finally {
      setUploading(null)
      if (faceInputRef.current) faceInputRef.current.value = ''
    }
  }

  const handleFingerprintUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !criminalId) return
    setUploading('fingerprint')
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('finger_type', fpFingerType)
      await api.post(`/api/criminal-intelligence/${criminalId}/biometrics/fingerprints`, formData)
      toast.success('Fingerprint template extracted successfully')
      const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/fingerprints`)
      setFpData(res.data)
      fetchCriminal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Fingerprint upload failed')
    } finally {
      setUploading(null)
      if (fpInputRef.current) fpInputRef.current.value = ''
    }
  }

  const handleDnaSubmit = async () => {
    if (!dnaForm.dna_id || !criminalId) return
    setUploading('face')
    try {
      await api.post(`/api/criminal-intelligence/${criminalId}/biometrics/dna`, {
        dna_id: dnaForm.dna_id,
        sample_number: dnaForm.sample_number || null,
        laboratory: dnaForm.laboratory || null,
        collection_date: dnaForm.collection_date || null,
      })
      toast.success('DNA profile added successfully')
      const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/dna`)
      setDnaData(res.data)
      setShowDnaForm(false)
      setDnaForm({ dna_id: '', sample_number: '', laboratory: '', collection_date: '' })
      fetchCriminal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'DNA profile creation failed')
    } finally {
      setUploading(null)
    }
  }

  useEffect(() => {
    setActiveTab('overview')
    setExpandedBio(null)
    setFaceData([])
    setFpData([])
    setDnaData([])
    setLoading(true)
    fetchCriminal()
  }, [criminalId])

  const fetchCriminal = async () => {
    try {
      const response = await api.get(`/api/criminal-intelligence/${criminalId}`)
      setCriminal(response.data)
    } catch {
      navigate('/criminal-intel/profiles')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!criminalId) return
    if (!window.confirm(`Are you sure you want to delete the criminal record for "${criminal?.full_name}"? This action cannot be undone.`)) return
    try {
      await api.delete(`/api/criminal-intelligence/${criminalId}`)
      toast.success('Criminal record deleted successfully')
      navigate('/criminal-intel/profiles')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to delete criminal record')
    }
  }

  const startEditing = () => {
    if (!criminal) return
    setEditForm({
      full_name: criminal.full_name || '',
      father_name: criminal.father_name || '',
      date_of_birth: criminal.date_of_birth || '',
      gender: criminal.gender || 'male',
      nationality: criminal.nationality || '',
      occupation: criminal.occupation || '',
      height_cm: criminal.height_cm?.toString() || '',
      weight_kg: criminal.weight_kg?.toString() || '',
      build: criminal.build || '',
      complexion: criminal.complexion || '',
      hair_color: criminal.hair_color || '',
      eye_color: criminal.eye_color || '',
      identifying_marks: criminal.identifying_marks?.join(', ') || '',
      gang_name: criminal.gang_name || '',
      gang_role: criminal.gang_role || '',
      crime_categories: criminal.crime_categories?.join(', ') || '',
      modus_operandi: criminal.modus_operandi || '',
      wanted_status: criminal.wanted_status || 'not_wanted',
      danger_level: criminal.danger_level || 'low',
      reward_amount: criminal.reward_amount?.toString() || '',
      notes: criminal.notes || '',
      station_id: '',
    })
    setEditing(true)
  }

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setEditForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleEditSave = async () => {
    if (!criminalId || !editForm.full_name.trim()) {
      toast.error('Full name is required')
      return
    }
    setEditSaving(true)
    try {
      const payload: Record<string, unknown> = {
        full_name: editForm.full_name.trim(),
        gender: editForm.gender,
        nationality: editForm.nationality || 'Indian',
        wanted_status: editForm.wanted_status,
        danger_level: editForm.danger_level,
      }
      if (editForm.father_name) payload.father_name = editForm.father_name
      else payload.father_name = null
      if (editForm.date_of_birth) payload.date_of_birth = editForm.date_of_birth
      else payload.date_of_birth = null
      if (editForm.occupation) payload.occupation = editForm.occupation
      else payload.occupation = null
      if (editForm.height_cm) payload.height_cm = parseFloat(editForm.height_cm)
      else payload.height_cm = null
      if (editForm.weight_kg) payload.weight_kg = parseFloat(editForm.weight_kg)
      else payload.weight_kg = null
      if (editForm.build) payload.build = editForm.build
      else payload.build = null
      if (editForm.complexion) payload.complexion = editForm.complexion
      else payload.complexion = null
      if (editForm.hair_color) payload.hair_color = editForm.hair_color
      else payload.hair_color = null
      if (editForm.eye_color) payload.eye_color = editForm.eye_color
      else payload.eye_color = null
      payload.identifying_marks = editForm.identifying_marks ? editForm.identifying_marks.split(',').map(s => s.trim()).filter(Boolean) : []
      if (editForm.gang_name) payload.gang_name = editForm.gang_name
      else payload.gang_name = null
      if (editForm.gang_role) payload.gang_role = editForm.gang_role
      else payload.gang_role = null
      payload.crime_categories = editForm.crime_categories ? editForm.crime_categories.split(',').map(s => s.trim()).filter(Boolean) : []
      if (editForm.modus_operandi) payload.modus_operandi = editForm.modus_operandi
      else payload.modus_operandi = null
      if (editForm.reward_amount) payload.reward_amount = parseFloat(editForm.reward_amount)
      else payload.reward_amount = null
      if (editForm.notes) payload.notes = editForm.notes
      else payload.notes = null

      await api.put(`/api/criminal-intelligence/${criminalId}`, payload)
      toast.success('Criminal profile updated successfully')
      setEditing(false)
      fetchCriminal()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to update profile')
    } finally {
      setEditSaving(false)
    }
  }

  const getCriminalIdStr = (pkId: number): string => {
    return `CR-${String(pkId).padStart(4, '0')}`
  }

  const toggleBiometric = async (type: 'face' | 'fingerprint' | 'dna') => {
    if (expandedBio === type) {
      setExpandedBio(null)
      return
    }
    setExpandedBio(type)
    setBioLoading(true)
    try {
      if (type === 'face') {
        const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/faces`)
        setFaceData(res.data)
      } else if (type === 'fingerprint') {
        const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/fingerprints`)
        setFpData(res.data)
      } else {
        const res = await api.get(`/api/criminal-intelligence/${criminalId}/biometrics/dna`)
        setDnaData(res.data)
      }
    } catch { /* silently fail — show empty */ }
    finally { setBioLoading(false) }
  }

  if (loading || !criminal) {
    return (
      <div className="space-y-4 p-6">
        <div className="h-8 w-48 skeleton" />
        <div className="h-64 skeleton" />
      </div>
    )
  }

  const dangerColors: Record<string, string> = {
    low: 'text-green-400 bg-green-500/10 border-green-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    extreme: 'text-red-400 bg-red-500/10 border-red-500/20',
  }

  const tabs = [
    { key: 'overview', label: 'Overview', icon: User },
    { key: 'cases', label: 'Case History', icon: FileText },
    { key: 'associates', label: 'Associates', icon: Users },
    { key: 'timeline', label: 'Timeline', icon: Clock },
    { key: 'biometrics', label: 'Biometrics', icon: Fingerprint },
  ] as const

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/criminal-intel/profiles')} className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-white">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{criminal.full_name}</h1>
            <span className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase border ${dangerColors[criminal.danger_level]}`}>
              {criminal.danger_level}
            </span>
            {criminal.wanted_status !== 'not_wanted' && (
              <span className="px-2.5 py-1 rounded text-[10px] font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/30">
                {criminal.wanted_status.replace('_', ' ')}
              </span>
            )}
          </div>
          <p className="text-dark-400 text-sm mt-1">
            {criminal.criminal_id} • {criminal.nicknames?.length ? `aka "${criminal.nicknames.join('", "')}"` : 'No aliases'}
            {criminal.gang_name && ` • ${criminal.gang_name}`}
          </p>
        </div>
        {criminal.reward_amount && (
          <div className="text-right">
            <p className="text-xs text-dark-400">Reward</p>
            <p className="text-lg font-bold text-amber-400">₹{criminal.reward_amount.toLocaleString()}</p>
          </div>
        )}
        <button
          onClick={startEditing}
          className="p-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:text-blue-300 transition-colors"
          title="Edit Criminal Profile"
        >
          <Pen className="w-5 h-5" />
        </button>
        <button
          onClick={handleDelete}
          className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 transition-colors"
          title="Delete Criminal Record"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      {/* Edit Form */}
      {editing && (
        <div className="bg-dark-900/80 border border-blue-500/30 rounded-xl p-6 space-y-5">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-bold text-white">Edit Criminal Profile</h2>
            <button onClick={() => setEditing(false)} className="p-1.5 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Personal Info */}
          <div>
            <h3 className="text-xs font-semibold text-purple-400 mb-3">Personal Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-dark-300 mb-1">Full Name *</label>
                <input name="full_name" value={editForm.full_name} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Father's Name</label>
                <input name="father_name" value={editForm.father_name} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Date of Birth</label>
                <input name="date_of_birth" type="date" value={editForm.date_of_birth} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Gender</label>
                <select name="gender" value={editForm.gender} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none">
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Nationality</label>
                <input name="nationality" value={editForm.nationality} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Occupation</label>
                <input name="occupation" value={editForm.occupation} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
            </div>
          </div>

          {/* Physical Description */}
          <div>
            <h3 className="text-xs font-semibold text-blue-400 mb-3">Physical Description</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-dark-300 mb-1">Height (cm)</label>
                <input name="height_cm" type="number" value={editForm.height_cm} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Weight (kg)</label>
                <input name="weight_kg" type="number" value={editForm.weight_kg} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Build</label>
                <input name="build" value={editForm.build} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Complexion</label>
                <input name="complexion" value={editForm.complexion} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Hair Color</label>
                <input name="hair_color" value={editForm.hair_color} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Eye Color</label>
                <input name="eye_color" value={editForm.eye_color} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
            </div>
            <div className="mt-3">
              <label className="block text-xs text-dark-300 mb-1">Identifying Marks (comma-separated)</label>
              <input name="identifying_marks" value={editForm.identifying_marks} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
            </div>
          </div>

          {/* Criminal Info */}
          <div>
            <h3 className="text-xs font-semibold text-red-400 mb-3">Criminal Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-dark-300 mb-1">Gang Name</label>
                <input name="gang_name" value={editForm.gang_name} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Gang Role</label>
                <input name="gang_role" value={editForm.gang_role} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Crime Categories (comma-separated)</label>
                <input name="crime_categories" value={editForm.crime_categories} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Reward Amount (₹)</label>
                <input name="reward_amount" type="number" value={editForm.reward_amount} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Wanted Status</label>
                <select name="wanted_status" value={editForm.wanted_status} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none">
                  {['not_wanted', 'wanted', 'most_wanted', 'surrendered', 'arrested', 'absconding'].map(s => (
                    <option key={s} value={s}>{s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-dark-300 mb-1">Danger Level</label>
                <select name="danger_level" value={editForm.danger_level} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none">
                  {['low', 'medium', 'high', 'extreme'].map(d => (
                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-3">
              <label className="block text-xs text-dark-300 mb-1">Modus Operandi</label>
              <textarea name="modus_operandi" value={editForm.modus_operandi} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none h-20 resize-none" />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs text-dark-300 mb-1">Notes</label>
            <textarea name="notes" value={editForm.notes} onChange={handleEditChange} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none h-20 resize-none" />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={() => setEditing(false)} className="px-4 py-2 rounded-lg bg-dark-700 hover:bg-dark-600 text-dark-300 text-sm font-medium transition-colors">
              Cancel
            </button>
            <button onClick={handleEditSave} disabled={editSaving} className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium flex items-center gap-2 disabled:opacity-50 transition-colors">
              {editSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {editSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Total FIRs', value: criminal.total_firs, color: 'text-red-400' },
          { label: 'Arrests', value: criminal.total_arrests, color: 'text-amber-400' },
          { label: 'Convictions', value: criminal.total_convictions, color: 'text-orange-400' },
          { label: 'Face Records', value: criminal.face_embeddings_count, color: 'text-emerald-400' },
          { label: 'Fingerprints', value: criminal.fingerprints_count, color: 'text-purple-400' },
        ].map(s => (
          <div key={s.label} className="rounded-xl bg-dark-800/50 border border-dark-700/50 p-3 text-center">
            <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-dark-400 uppercase mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-dark-800/50 p-1 rounded-xl border border-dark-700/50">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.key
                ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                : 'text-dark-400 hover:text-white'
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Personal Information */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <User className="w-4 h-4 text-emerald-400" /> Personal Information
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-dark-400">Father:</span> <span className="text-white ml-2">{criminal.father_name || '—'}</span></div>
              <div><span className="text-dark-400">DOB:</span> <span className="text-white ml-2">{criminal.date_of_birth || '—'}</span></div>
              <div><span className="text-dark-400">Gender:</span> <span className="text-white ml-2 capitalize">{criminal.gender}</span></div>
              <div><span className="text-dark-400">Nationality:</span> <span className="text-white ml-2">{criminal.nationality}</span></div>
              <div><span className="text-dark-400">Occupation:</span> <span className="text-white ml-2">{criminal.occupation || '—'}</span></div>
              <div><span className="text-dark-400">Education:</span> <span className="text-white ml-2">{criminal.education || '—'}</span></div>
              <div><span className="text-dark-400">Height:</span> <span className="text-white ml-2">{criminal.height_cm ? `${criminal.height_cm} cm` : '—'}</span></div>
              <div><span className="text-dark-400">Weight:</span> <span className="text-white ml-2">{criminal.weight_kg ? `${criminal.weight_kg} kg` : '—'}</span></div>
              <div><span className="text-dark-400">Build:</span> <span className="text-white ml-2 capitalize">{criminal.build || '—'}</span></div>
              <div><span className="text-dark-400">Complexion:</span> <span className="text-white ml-2 capitalize">{criminal.complexion || '—'}</span></div>
            </div>
            {criminal.identifying_marks && criminal.identifying_marks.length > 0 && (
              <div className="mt-3 pt-3 border-t border-dark-700/50">
                <span className="text-dark-400 text-xs">Identifying Marks:</span>
                <p className="text-white text-sm mt-1">{criminal.identifying_marks.join(', ')}</p>
              </div>
            )}
          </motion.div>

          {/* Criminal Activity */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <BadgeAlert className="w-4 h-4 text-red-400" /> Criminal Activity
            </h3>
            <div className="space-y-3 text-sm">
              <div><span className="text-dark-400">Gang:</span> <span className="text-white ml-2">{criminal.gang_name || 'Independent'} {criminal.gang_role ? `(${criminal.gang_role})` : ''}</span></div>
              <div><span className="text-dark-400">Crime Categories:</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(criminal.crime_categories ?? []).map(cat => (
                    <span key={cat} className="px-2 py-0.5 text-[10px] bg-red-500/10 text-red-300 border border-red-500/20 rounded capitalize">{cat.replace('_', ' ')}</span>
                  ))}
                </div>
              </div>
              <div><span className="text-dark-400">Known Weapons:</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(criminal.known_weapons ?? []).map(w => (
                    <span key={w} className="px-2 py-0.5 text-[10px] bg-amber-500/10 text-amber-300 border border-amber-500/20 rounded">{w}</span>
                  ))}
                </div>
              </div>
              {criminal.modus_operandi && (
                <div><span className="text-dark-400">Modus Operandi:</span><p className="text-dark-200 mt-1">{criminal.modus_operandi}</p></div>
              )}
              <div><span className="text-dark-400">First Offense:</span> <span className="text-white ml-2">{criminal.first_offense_date || '—'}</span></div>
              <div><span className="text-dark-400">Last Activity:</span> <span className="text-white ml-2">{criminal.last_known_activity ? new Date(criminal.last_known_activity).toLocaleDateString() : '—'}</span></div>
            </div>
          </motion.div>

          {/* Addresses */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-400" /> Known Addresses ({criminal.addresses.length})
            </h3>
            <div className="space-y-3">
              {criminal.addresses.map((addr, i) => (
                <div key={i} className="p-3 rounded-lg bg-dark-800/50 border border-dark-700/30">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] uppercase text-dark-400">{addr.address_type}</span>
                    {addr.is_current && <span className="text-[9px] text-emerald-400 bg-emerald-500/10 px-1.5 rounded">CURRENT</span>}
                  </div>
                  <p className="text-sm text-white">{addr.address_line}</p>
                  <p className="text-xs text-dark-400">{addr.city}{addr.state ? `, ${addr.state}` : ''}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Vehicles */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Car className="w-4 h-4 text-amber-400" /> Known Vehicles ({criminal.vehicles.length})
            </h3>
            <div className="space-y-3">
              {criminal.vehicles.map((v, i) => (
                <div key={i} className="p-3 rounded-lg bg-dark-800/50 border border-dark-700/30 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-white">{v.make} {v.model} <span className="text-dark-400">({v.color})</span></p>
                    <p className="text-xs text-dark-400 capitalize">{v.vehicle_type}</p>
                  </div>
                  <div className="text-right">
                    {v.registration_number && <p className="text-sm font-mono text-emerald-400">{v.registration_number}</p>}
                    {v.is_stolen && <span className="text-[9px] text-red-400 bg-red-500/10 px-1.5 rounded">STOLEN</span>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Phone Numbers */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Phone className="w-4 h-4 text-green-400" /> Phone Numbers ({criminal.phone_numbers.length})
            </h3>
            <div className="space-y-2">
              {criminal.phone_numbers.map((p, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-dark-800/50">
                  <span className="text-sm font-mono text-white">{p.phone_number}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-dark-400 capitalize">{p.phone_type}</span>
                    <span className={`w-2 h-2 rounded-full ${p.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Social Accounts */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Globe className="w-4 h-4 text-cyan-400" /> Social Media ({criminal.social_accounts.length})
            </h3>
            <div className="space-y-2">
              {criminal.social_accounts.map((s, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-dark-800/50">
                  <div>
                    <span className="text-sm text-white capitalize">{s.platform}</span>
                    <span className="text-xs text-dark-400 ml-2">@{s.username}</span>
                  </div>
                  <span className={`w-2 h-2 rounded-full ${s.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {activeTab === 'cases' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-900/50">
                <tr>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">FIR No.</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Type</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Sections</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Station</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Date</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Status</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800/50">
                {criminal.case_history.map((ch, i) => (
                  <tr key={i} className="hover:bg-dark-800/30">
                    <td className="px-5 py-3 text-sm font-mono text-emerald-400">{ch.fir_number || '—'}</td>
                    <td className="px-5 py-3 text-sm text-white capitalize">{ch.case_type.replace('_', ' ')}</td>
                    <td className="px-5 py-3 text-xs text-dark-300">{(ch.sections_applied ?? []).join(', ') || '—'}</td>
                    <td className="px-5 py-3 text-xs text-dark-300">{ch.police_station || '—'}</td>
                    <td className="px-5 py-3 text-xs text-dark-300">{ch.date_of_offense || '—'}</td>
                    <td className="px-5 py-3">
                      <span className="text-xs text-amber-400 capitalize">{ch.case_status || '—'}</span>
                    </td>
                    <td className="px-5 py-3 text-xs text-dark-300 capitalize">{ch.verdict || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {activeTab === 'associates' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          {criminal.associates.length === 0 ? (
            <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-10 text-center">
              <Users className="w-12 h-12 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400 text-sm">No known associates</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {criminal.associates.map((a, i) => {
                const linkedId = a.associate_criminal_id ? getCriminalIdStr(a.associate_criminal_id) : null
                return (
                  <motion.div
                    key={a.id || i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => {
                      if (linkedId) {
                        navigate(`/criminal-intel/profiles/${linkedId}`)
                      }
                    }}
                    className={`rounded-xl bg-dark-900/80 border border-dark-700/50 p-4 transition-all ${
                      linkedId
                        ? 'cursor-pointer hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5'
                        : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        linkedId ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-dark-700'
                      }`}>
                        <Users className={`w-5 h-5 ${linkedId ? 'text-emerald-400' : 'text-dark-400'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-white truncate">{a.associate_name}</p>
                          {linkedId && <ExternalLink className="w-3 h-3 text-emerald-400 flex-shrink-0" />}
                        </div>
                        <p className="text-xs text-dark-400 capitalize">{a.relationship_type.replace('_', ' ')}</p>
                      </div>
                    </div>
                    {a.gang_connection && (
                      <p className="text-xs text-emerald-400 mt-2 ml-[52px]">Gang: {a.gang_connection}</p>
                    )}
                    {a.notes && (
                      <p className="text-xs text-dark-500 mt-1 ml-[52px] truncate">{a.notes}</p>
                    )}
                    {linkedId && (
                      <p className="text-[10px] text-emerald-500/60 mt-2 ml-[52px]">Click to view profile</p>
                    )}
                  </motion.div>
                )
              })}
            </div>
          )}
        </motion.div>
      )}

      {activeTab === 'timeline' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative pl-8">
          <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-dark-700" />
          {criminal.timeline.sort((a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime()).map((event, i) => (
            <div key={i} className="relative mb-6">
              <div className="absolute -left-5 top-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-dark-900" />
              <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-4 ml-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-emerald-400 font-medium capitalize">{event.event_type.replace('_', ' ')}</span>
                  <span className="text-xs text-dark-400">{event.event_date}</span>
                </div>
                <p className="text-sm font-medium text-white">{event.title}</p>
                {event.description && <p className="text-xs text-dark-300 mt-1">{event.description}</p>}
                {event.location && <p className="text-xs text-dark-400 mt-1 flex items-center gap-1"><MapPin className="w-3 h-3" />{event.location}</p>}
              </div>
            </div>
          ))}
        </motion.div>
      )}

      {activeTab === 'biometrics' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          {/* Hidden file inputs */}
          <input ref={faceInputRef} type="file" accept="image/jpeg,image/png,image/bmp,image/tiff,image/webp" className="hidden" onChange={handleFaceUpload} />
          <input ref={fpInputRef} type="file" accept="image/jpeg,image/png,image/bmp,image/tiff,image/webp" className="hidden" onChange={handleFingerprintUpload} />

          {/* Face Embeddings */}
          <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden">
            <div className="flex items-center justify-between p-5">
              <button
                onClick={() => toggleBiometric('face')}
                className="flex items-center gap-4 flex-1 text-left hover:opacity-80 transition-opacity"
              >
                <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
                  <Eye className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <p className="text-white font-semibold">Face Embeddings</p>
                  <p className="text-xs text-dark-400">{criminal.face_embeddings_count} records • 512-dim vectors for recognition</p>
                </div>
              </button>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => faceInputRef.current?.click()}
                  disabled={uploading === 'face'}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                >
                  {uploading === 'face' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  Upload Face
                </button>
                <span className="text-2xl font-bold text-emerald-400">{criminal.face_embeddings_count}</span>
                <button onClick={() => toggleBiometric('face')}>
                  {expandedBio === 'face' ? <ChevronUp className="w-5 h-5 text-dark-400" /> : <ChevronDown className="w-5 h-5 text-dark-400" />}
                </button>
              </div>
            </div>
            {expandedBio === 'face' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="border-t border-dark-700/50 p-5">
                {bioLoading ? (
                  <div className="text-center py-6">
                    <div className="w-6 h-6 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-dark-400">Loading face data...</p>
                  </div>
                ) : faceData.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-xs text-dark-400 mb-3">Stored face embeddings ({faceData.length} records):</p>
                    <div className="space-y-4">
                      {faceData.map((face, i) => (
                        <div key={face.id} className="rounded-lg bg-dark-800/50 border border-emerald-500/10 p-4">
                          <div className="flex items-start gap-4">
                            <div className="w-14 h-14 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                              <Eye className="w-6 h-6 text-emerald-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-white">Face Record #{i + 1}</p>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 mt-2">
                                <div>
                                  <span className="text-[10px] text-dark-500">Model</span>
                                  <p className="text-xs text-dark-300">{face.model_name === 'insightface_buffalo' ? 'InsightFace Buffalo' : face.model_name}</p>
                                </div>
                                <div>
                                  <span className="text-[10px] text-dark-500">Dimensions</span>
                                  <p className="text-xs text-dark-300">{face.embedding_dim}-dim vector</p>
                                </div>
                                {face.quality_score !== null && (
                                  <div>
                                    <span className="text-[10px] text-dark-500">Quality</span>
                                    <p className="text-xs text-emerald-400">{(face.quality_score * 100).toFixed(1)}%</p>
                                  </div>
                                )}
                                {face.created_at && (
                                  <div>
                                    <span className="text-[10px] text-dark-500">Captured</span>
                                    <p className="text-xs text-dark-300">{new Date(face.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          {face.embedding && face.embedding.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-dark-700/30">
                              <p className="text-[10px] text-dark-500 mb-2">Embedding Vector ({face.embedding.length} floats)</p>
                              <div className="bg-dark-900/80 rounded-lg p-3 max-h-32 overflow-y-auto font-mono text-[10px] text-emerald-300/70 leading-relaxed break-all">
                                [{face.embedding.slice(0, 50).map(v => v.toFixed(4)).join(', ')}{face.embedding.length > 50 ? `, ... (${face.embedding.length - 50} more)` : ''}]
                              </div>
                              <div className="flex gap-4 mt-2">
                                <span className="text-[9px] text-dark-500">Min: {Math.min(...face.embedding).toFixed(4)}</span>
                                <span className="text-[9px] text-dark-500">Max: {Math.max(...face.embedding).toFixed(4)}</span>
                                <span className="text-[9px] text-dark-500">Norm: {Math.sqrt(face.embedding.reduce((s, v) => s + v * v, 0)).toFixed(4)}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <Image className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                    <p className="text-sm text-dark-400">No face embeddings recorded</p>
                    <button
                      onClick={() => faceInputRef.current?.click()}
                      disabled={uploading === 'face'}
                      className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                    >
                      {uploading === 'face' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                      Upload Face Photo
                    </button>
                    <p className="text-xs text-dark-500 mt-2">Accepts JPEG, PNG, BMP, TIFF, WebP (max 10MB)</p>
                  </div>
                )}
              </motion.div>
            )}
          </div>

          {/* Fingerprints */}
          <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden">
            <div className="flex items-center justify-between p-5">
              <button
                onClick={() => toggleBiometric('fingerprint')}
                className="flex items-center gap-4 flex-1 text-left hover:opacity-80 transition-opacity"
              >
                <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center">
                  <Fingerprint className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <p className="text-white font-semibold">Fingerprint Templates</p>
                  <p className="text-xs text-dark-400">{criminal.fingerprints_count} records • Minutiae data for matching</p>
                </div>
              </button>
              <div className="flex items-center gap-3">
                <select
                  value={fpFingerType}
                  onChange={(e) => setFpFingerType(e.target.value)}
                  className="text-[10px] bg-dark-800 border border-dark-700 rounded-md px-2 py-1 text-dark-300 focus:outline-none focus:border-purple-500/50"
                >
                  <option value="right_thumb">R Thumb</option>
                  <option value="right_index">R Index</option>
                  <option value="right_middle">R Middle</option>
                  <option value="right_ring">R Ring</option>
                  <option value="right_little">R Little</option>
                  <option value="left_thumb">L Thumb</option>
                  <option value="left_index">L Index</option>
                  <option value="left_middle">L Middle</option>
                  <option value="left_ring">L Ring</option>
                  <option value="left_little">L Little</option>
                </select>
                <button
                  onClick={() => fpInputRef.current?.click()}
                  disabled={uploading === 'fingerprint'}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-medium hover:bg-purple-500/20 transition-colors disabled:opacity-50"
                >
                  {uploading === 'fingerprint' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  Upload
                </button>
                <span className="text-2xl font-bold text-purple-400">{criminal.fingerprints_count}</span>
                <button onClick={() => toggleBiometric('fingerprint')}>
                  {expandedBio === 'fingerprint' ? <ChevronUp className="w-5 h-5 text-dark-400" /> : <ChevronDown className="w-5 h-5 text-dark-400" />}
                </button>
              </div>
            </div>
            {expandedBio === 'fingerprint' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="border-t border-dark-700/50 p-5">
                {bioLoading ? (
                  <div className="text-center py-6">
                    <div className="w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-dark-400">Loading fingerprint data...</p>
                  </div>
                ) : fpData.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-xs text-dark-400 mb-3">Stored fingerprint records ({fpData.length}):</p>
                    {fpData.map((fp) => (
                      <div key={fp.id} className="rounded-lg bg-dark-800/50 border border-purple-500/10 p-4">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
                            <Fingerprint className="w-5 h-5 text-purple-400" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white capitalize">{fp.finger_type.replace('_', ' ')}</p>
                            <div className="flex items-center gap-4 mt-1">
                              {fp.quality_score !== null && (
                                <span className="text-[10px] text-purple-400">Quality: {(fp.quality_score * 100).toFixed(0)}%</span>
                              )}
                              {fp.template_data?.minutiae_count && (
                                <span className="text-[10px] text-dark-400">Minutiae: {fp.template_data.minutiae_count}</span>
                              )}
                              {fp.created_at && (
                                <span className="text-[10px] text-dark-500">{new Date(fp.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {fp.template_data && (
                          <div className="mt-3 pt-3 border-t border-dark-700/30">
                            {fp.template_data.keypoints && fp.template_data.keypoints.length > 0 && (
                              <div className="mb-2">
                                <p className="text-[10px] text-dark-500 mb-1.5">Keypoints ({fp.template_data.keypoints.length} minutiae points)</p>
                                <div className="bg-dark-900/80 rounded-lg p-3 max-h-28 overflow-y-auto font-mono text-[10px] text-purple-300/70 leading-relaxed">
                                  {fp.template_data.keypoints.slice(0, 20).map((kp, idx) => (
                                    <span key={idx}>({kp.x}, {kp.y}) ∠{kp.angle.toFixed(0)}° s={kp.size.toFixed(1)}{idx < Math.min(19, fp.template_data!.keypoints!.length - 1) ? ' • ' : ''}</span>
                                  ))}
                                  {fp.template_data.keypoints.length > 20 && <span className="text-dark-500"> ... +{fp.template_data.keypoints.length - 20} more</span>}
                                </div>
                              </div>
                            )}
                            {fp.template_data.descriptors && fp.template_data.descriptors.length > 0 && (
                              <div>
                                <p className="text-[10px] text-dark-500 mb-1.5">ORB Descriptors ({fp.template_data.descriptors.length} × {fp.template_data.descriptors[0]?.length || 32} matrix)</p>
                                <div className="bg-dark-900/80 rounded-lg p-3 max-h-24 overflow-y-auto font-mono text-[9px] text-purple-300/50 leading-relaxed break-all">
                                  [{fp.template_data.descriptors.slice(0, 3).map(row => `[${row.slice(0, 8).join(',')}...]`).join(', ')}{fp.template_data.descriptors.length > 3 ? `, ... (${fp.template_data.descriptors.length - 3} more rows)` : ''}]
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <Fingerprint className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                    <p className="text-sm text-dark-400">No fingerprint templates recorded</p>
                    <button
                      onClick={() => fpInputRef.current?.click()}
                      disabled={uploading === 'fingerprint'}
                      className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 text-sm font-medium hover:bg-purple-500/20 transition-colors disabled:opacity-50"
                    >
                      {uploading === 'fingerprint' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                      Upload Fingerprint
                    </button>
                    <p className="text-xs text-dark-500 mt-2">Select finger type above, then upload scan image</p>
                  </div>
                )}
              </motion.div>
            )}
          </div>

          {/* DNA Profiles */}
          <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden">
            <div className="flex items-center justify-between p-5">
              <button
                onClick={() => toggleBiometric('dna')}
                className="flex items-center gap-4 flex-1 text-left hover:opacity-80 transition-opacity"
              >
                <div className="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center">
                  <Dna className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <p className="text-white font-semibold">DNA Profiles</p>
                  <p className="text-xs text-dark-400">{criminal.dna_profiles_count} records • CODIS loci markers</p>
                </div>
              </button>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => { setShowDnaForm(true); setExpandedBio('dna') }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-medium hover:bg-cyan-500/20 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add DNA
                </button>
                <span className="text-2xl font-bold text-cyan-400">{criminal.dna_profiles_count}</span>
                <button onClick={() => toggleBiometric('dna')}>
                  {expandedBio === 'dna' ? <ChevronUp className="w-5 h-5 text-dark-400" /> : <ChevronDown className="w-5 h-5 text-dark-400" />}
                </button>
              </div>
            </div>
            {expandedBio === 'dna' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="border-t border-dark-700/50 p-5">
                {bioLoading ? (
                  <div className="text-center py-6">
                    <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-dark-400">Loading DNA data...</p>
                  </div>
                ) : dnaData.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-xs text-dark-400 mb-3">Stored DNA profiles ({dnaData.length}):</p>
                    {dnaData.map((dna) => (
                      <div key={dna.id} className="rounded-lg bg-dark-800/50 border border-cyan-500/10 p-4">
                        <div className="flex items-center gap-3 mb-3">
                          <Dna className="w-5 h-5 text-cyan-400" />
                          <span className="text-sm font-semibold text-white">{dna.dna_id}</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          {dna.sample_number && (
                            <div>
                              <span className="text-[10px] text-dark-500">Sample #</span>
                              <p className="text-xs text-dark-300">{dna.sample_number}</p>
                            </div>
                          )}
                          {dna.laboratory && (
                            <div>
                              <span className="text-[10px] text-dark-500">Laboratory</span>
                              <p className="text-xs text-dark-300">{dna.laboratory}</p>
                            </div>
                          )}
                          {dna.collection_date && (
                            <div>
                              <span className="text-[10px] text-dark-500">Collection Date</span>
                              <p className="text-xs text-dark-300">{new Date(dna.collection_date).toLocaleDateString()}</p>
                            </div>
                          )}
                          {dna.created_at && (
                            <div>
                              <span className="text-[10px] text-dark-500">Recorded</span>
                              <p className="text-xs text-dark-300">{new Date(dna.created_at).toLocaleDateString()}</p>
                            </div>
                          )}
                        </div>
                        {dna.loci_markers && Object.keys(dna.loci_markers).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-dark-700/30">
                            <p className="text-[10px] text-dark-500 mb-2">CODIS Loci Markers ({Object.keys(dna.loci_markers).length} loci)</p>
                            <div className="flex flex-wrap gap-1.5">
                              {Object.entries(dna.loci_markers).slice(0, 20).map(([locus, alleles]) => (
                                <span key={locus} className="px-2 py-0.5 rounded bg-cyan-500/5 border border-cyan-500/15 text-[9px] text-cyan-300">
                                  {locus}: {String(alleles)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {dna.profile_data && Object.keys(dna.profile_data).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-dark-700/30">
                            <p className="text-[10px] text-dark-500 mb-2">Profile Data</p>
                            <div className="bg-dark-900/80 rounded-lg p-3 max-h-32 overflow-y-auto font-mono text-[10px] text-cyan-300/70 leading-relaxed">
                              {Object.entries(dna.profile_data).map(([key, value]) => (
                                <div key={key} className="flex gap-2 mb-0.5">
                                  <span className="text-dark-500 flex-shrink-0">{key}:</span>
                                  <span className="text-cyan-300/80 break-all">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : !showDnaForm ? (
                  <div className="text-center py-6">
                    <Dna className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                    <p className="text-sm text-dark-400">No DNA profiles recorded</p>
                    <button
                      onClick={() => setShowDnaForm(true)}
                      className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm font-medium hover:bg-cyan-500/20 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Add DNA Profile
                    </button>
                  </div>
                ) : null}
                {showDnaForm && (
                  <div className="rounded-lg bg-dark-800/50 border border-cyan-500/20 p-4 mt-3">
                    <p className="text-sm font-medium text-white mb-3">Add DNA Profile</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input
                        type="text"
                        placeholder="DNA ID (e.g. DNA-001) *"
                        value={dnaForm.dna_id}
                        onChange={(e) => setDnaForm(f => ({ ...f, dna_id: e.target.value }))}
                        className="px-3 py-2 rounded-lg bg-dark-900 border border-dark-700 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-cyan-500/50"
                      />
                      <input
                        type="text"
                        placeholder="Sample Number"
                        value={dnaForm.sample_number}
                        onChange={(e) => setDnaForm(f => ({ ...f, sample_number: e.target.value }))}
                        className="px-3 py-2 rounded-lg bg-dark-900 border border-dark-700 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-cyan-500/50"
                      />
                      <input
                        type="text"
                        placeholder="Laboratory"
                        value={dnaForm.laboratory}
                        onChange={(e) => setDnaForm(f => ({ ...f, laboratory: e.target.value }))}
                        className="px-3 py-2 rounded-lg bg-dark-900 border border-dark-700 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-cyan-500/50"
                      />
                      <input
                        type="date"
                        value={dnaForm.collection_date}
                        onChange={(e) => setDnaForm(f => ({ ...f, collection_date: e.target.value }))}
                        className="px-3 py-2 rounded-lg bg-dark-900 border border-dark-700 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-cyan-500/50"
                      />
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <button
                        onClick={handleDnaSubmit}
                        disabled={!dnaForm.dna_id}
                        className="px-4 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 text-xs font-medium hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
                      >
                        Save DNA Profile
                      </button>
                      <button
                        onClick={() => setShowDnaForm(false)}
                        className="px-4 py-2 rounded-lg bg-dark-800 border border-dark-700 text-dark-400 text-xs font-medium hover:bg-dark-700 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}
 
