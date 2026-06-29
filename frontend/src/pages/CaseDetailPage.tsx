import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText,
  Upload,
  Brain,
  BookOpen,
  Calendar,
  MapPin,
  User,
  Shield,
} from 'lucide-react'
import api from '../api/client'

interface CaseDetail {
  id: number
  fir_number: string
  complainant_name: string
  complainant_contact: string | null
  complainant_address: string | null
  accused_name: string | null
  incident_date: string | null
  incident_time: string | null
  incident_location: string | null
  description: string
  extracted_data: Record<string, unknown> | null
  status: string
  assigned_officer_id: number | null
  sections_applied: string[] | null
  offense_type: string | null
  created_at: string
  updated_at: string
}

export default function CaseDetailPage() {
  const { id } = useParams()
  const [caseData, setCaseData] = useState<CaseDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCase()
  }, [id])

  const loadCase = async () => {
    try {
      const response = await api.get(`/api/cases/${id}`)
      setCaseData(response.data)
    } catch {
      setCaseData(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-dark-400">Loading case...</div>
  }

  if (!caseData) {
    return <div className="flex items-center justify-center h-64 text-dark-400">Case not found</div>
  }

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    investigating: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    chargesheet_filed: 'bg-green-500/20 text-green-400 border-green-500/30',
    closed: 'bg-dark-500/20 text-dark-300 border-dark-500/30',
  }

  const actions = [
    { label: 'Evidence', icon: Upload, path: `/evidence/${id}`, color: 'text-purple-400' },
    { label: 'Investigate', icon: Brain, path: `/investigation/${id}`, color: 'text-yellow-400' },
    { label: 'Documents', icon: FileText, path: `/documents/${id}`, color: 'text-green-400' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Case: {caseData.fir_number}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusColors[caseData.status]}`}>
              {caseData.status.replace('_', ' ').toUpperCase()}
            </span>
            {caseData.offense_type && (
              <span className="text-dark-400 text-sm">{caseData.offense_type}</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {actions.map((action, i) => (
          <motion.div
            key={action.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Link
              to={action.path}
              className="card flex items-center gap-4 hover:border-primary-600/50 transition-colors"
            >
              <action.icon className={`w-8 h-8 ${action.color}`} />
              <span className="text-white font-medium">{action.label}</span>
            </Link>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-primary-400" />
            Complainant Details
          </h2>
          <div className="space-y-3">
            <InfoRow label="Name" value={caseData.complainant_name} />
            <InfoRow label="Contact" value={caseData.complainant_contact} />
            <InfoRow label="Address" value={caseData.complainant_address} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-400" />
            Incident Details
          </h2>
          <div className="space-y-3">
            <InfoRow label="Accused" value={caseData.accused_name} />
            <InfoRow label="Date" value={caseData.incident_date} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Time" value={caseData.incident_time} />
            <InfoRow label="Location" value={caseData.incident_location} icon={<MapPin className="w-4 h-4" />} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card lg:col-span-2"
        >
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-green-400" />
            Description
          </h2>
          <p className="text-dark-300 whitespace-pre-wrap leading-relaxed">{caseData.description}</p>
        </motion.div>

        {caseData.sections_applied && caseData.sections_applied.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="card lg:col-span-2"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Applicable Sections</h2>
            <div className="flex flex-wrap gap-2">
              {caseData.sections_applied.map((section, i) => (
                <span
                  key={i}
                  className="px-3 py-1.5 bg-primary-600/20 text-primary-400 rounded-lg text-sm border border-primary-600/30"
                >
                  {section}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

function InfoRow({ label, value, icon }: { label: string; value: string | null; icon?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      {icon && <span className="text-dark-400 mt-0.5">{icon}</span>}
      <span className="text-dark-400 text-sm min-w-[80px]">{label}:</span>
      <span className="text-white text-sm">{value || '—'}</span>
    </div>
  )
}
