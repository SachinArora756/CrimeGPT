import { Target, Box, AlertTriangle, Car, Armchair, Droplets, Footprints, Phone, MapPin } from 'lucide-react'

interface SceneObject {
  id: string
  type: string
  position: number[]
  rotation: number[]
  scale: number[]
  label: string
  color: string
  evidence_id: number | null
  photo_id: string | null
}

interface Props {
  objects: SceneObject[]
  selectedId: string | null
  onSelect: (id: string) => void
}

const typeIcons: Record<string, typeof Box> = {
  body_outline: Target,
  weapon_knife: AlertTriangle,
  weapon_gun: AlertTriangle,
  weapon_blunt: AlertTriangle,
  blood_stain: Droplets,
  vehicle: Car,
  furniture_table: Armchair,
  furniture_chair: Armchair,
  evidence_marker: MapPin,
  footprint: Footprints,
  mobile_phone: Phone,
}

const typeLabels: Record<string, string> = {
  body_outline: 'Body Position',
  weapon_knife: 'Weapon (Knife)',
  weapon_gun: 'Weapon (Gun)',
  weapon_blunt: 'Weapon (Blunt)',
  blood_stain: 'Blood Stain',
  vehicle: 'Vehicle',
  furniture_table: 'Table',
  furniture_chair: 'Chair',
  evidence_marker: 'Evidence',
  footprint: 'Footprint',
  mobile_phone: 'Phone',
  door: 'Door',
  window: 'Window',
  broken_glass: 'Broken Glass',
  clothing: 'Clothing',
  drug_substance: 'Drug/Substance',
  cash_money: 'Cash/Money',
  cctv_camera: 'CCTV',
}

export default function ObjectPanel({ objects, selectedId, onSelect }: Props) {
  return (
    <div className="bg-gray-900 border-l border-gray-700 w-64 overflow-y-auto">
      <div className="p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Scene Objects</h3>
        <p className="text-xs text-gray-500 mt-0.5">{objects.length} items placed</p>
      </div>
      <div className="divide-y divide-gray-800">
        {objects.map((obj) => {
          const Icon = typeIcons[obj.type] || Box
          const isSelected = obj.id === selectedId
          return (
            <button
              key={obj.id}
              onClick={() => onSelect(obj.id)}
              className={`w-full flex items-start gap-2 p-3 text-left hover:bg-gray-800 transition-colors ${isSelected ? 'bg-gray-800 border-l-2 border-purple-500' : ''}`}
            >
              <div
                className="mt-0.5 p-1.5 rounded"
                style={{ backgroundColor: `${obj.color}20` }}
              >
                <Icon size={14} style={{ color: obj.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-200 truncate">{obj.label}</p>
                <p className="text-[10px] text-gray-500">
                  {typeLabels[obj.type] || obj.type}
                </p>
                {obj.evidence_id && (
                  <span className="inline-block mt-1 px-1.5 py-0.5 bg-blue-900/50 text-blue-300 text-[9px] rounded">
                    Evidence #{obj.evidence_id}
                  </span>
                )}
              </div>
            </button>
          )
        })}
        {objects.length === 0 && (
          <div className="p-4 text-center text-xs text-gray-500">
            No objects in scene
          </div>
        )}
      </div>
    </div>
  )
}
