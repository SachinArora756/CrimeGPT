import { useRef, useMemo, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Text } from '@react-three/drei'
import * as THREE from 'three'

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

interface SceneLayout {
  width: number
  length: number
  height: number
  ground_type: string
  walls: any[]
  lighting: {
    time_of_day: string
    ambient_intensity: number
    main_light_position: number[]
  }
}

interface Props {
  layout: SceneLayout
  objects: SceneObject[]
  highlightedObjects: string[]
  cameraTarget?: { position: number[]; target: number[] } | null
  onObjectClick?: (id: string) => void
}

function CameraController({ target }: { target: { position: number[]; target: number[] } | null }) {
  const { camera } = useThree()
  const controlsRef = useRef<any>(null)

  useEffect(() => {
    if (target) {
      camera.position.set(target.position[0], target.position[1], target.position[2])
      if (controlsRef.current) {
        controlsRef.current.target.set(target.target[0], target.target[1], target.target[2])
      }
    }
  }, [target, camera])

  return <OrbitControls ref={controlsRef} enableDamping dampingFactor={0.1} />
}

function SceneObject3D({ obj, highlighted, onClick }: { obj: SceneObject; highlighted: boolean; onClick: () => void }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const color = useMemo(() => new THREE.Color(obj.color || '#FFD700'), [obj.color])

  useFrame((_, delta) => {
    if (meshRef.current && highlighted) {
      meshRef.current.rotation.y += delta * 0.5
    }
  })

  const pos = obj.position || [0, 0, 0]
  const emissiveIntensity = highlighted ? 0.6 : 0

  switch (obj.type) {
    case 'body_outline':
      return (
        <mesh ref={meshRef} position={[pos[0], 0.02, pos[2]]} rotation={[-Math.PI / 2, 0, 0]} onClick={onClick}>
          <planeGeometry args={[0.5, 1.8]} />
          <meshStandardMaterial color="#ffffff" transparent opacity={0.7} side={THREE.DoubleSide} emissive="#ffffff" emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    case 'weapon_knife':
    case 'weapon_gun':
    case 'weapon_blunt':
      return (
        <mesh ref={meshRef} position={[pos[0], pos[1] || 0.15, pos[2]]} rotation={[0, 0, Math.PI / 4]} onClick={onClick}>
          <cylinderGeometry args={[0.02, 0.02, 0.3, 8]} />
          <meshStandardMaterial color="#cc0000" metalness={0.8} emissive="#cc0000" emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    case 'blood_stain':
      return (
        <mesh ref={meshRef} position={[pos[0], 0.02, pos[2]]} rotation={[-Math.PI / 2, 0, 0]} onClick={onClick}>
          <circleGeometry args={[0.3, 16]} />
          <meshStandardMaterial color="#8B0000" transparent opacity={0.8} side={THREE.DoubleSide} emissive="#8B0000" emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    case 'vehicle':
      return (
        <mesh ref={meshRef} position={[pos[0], pos[1] || 0.75, pos[2]]} onClick={onClick}>
          <boxGeometry args={[2, 1.5, 4]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    case 'evidence_marker':
      return (
        <mesh ref={meshRef} position={[pos[0], 0.2, pos[2]]} onClick={onClick}>
          <coneGeometry args={[0.15, 0.4, 8]} />
          <meshStandardMaterial color="#FFD700" emissive="#886600" emissiveIntensity={highlighted ? 0.8 : 0.3} />
        </mesh>
      )
    case 'furniture_table':
      return (
        <mesh ref={meshRef} position={[pos[0], pos[1] || 0.4, pos[2]]} onClick={onClick}>
          <boxGeometry args={[1.2, 0.8, 0.8]} />
          <meshStandardMaterial color="#8B4513" emissive="#8B4513" emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    case 'furniture_chair':
      return (
        <mesh ref={meshRef} position={[pos[0], pos[1] || 0.45, pos[2]]} onClick={onClick}>
          <boxGeometry args={[0.5, 0.9, 0.5]} />
          <meshStandardMaterial color="#654321" emissive="#654321" emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
    default:
      return (
        <mesh ref={meshRef} position={[pos[0], pos[1] || 0.2, pos[2]]} onClick={onClick}>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} />
        </mesh>
      )
  }
}

function SceneEnvironment({ layout }: { layout: SceneLayout }) {
  const { width, length, height } = layout

  return (
    <>
      <mesh position={[width / 2, 0, length / 2]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[width, length]} />
        <meshStandardMaterial color="#333344" roughness={0.8} />
      </mesh>

      <gridHelper
        args={[Math.max(width, length), Math.max(width, length), '#444466', '#222244']}
        position={[width / 2, 0.01, length / 2]}
      />

      {height > 0 && layout.ground_type === 'floor' && (
        <>
          <mesh position={[width / 2, height / 2, 0]}>
            <planeGeometry args={[width, height]} />
            <meshStandardMaterial color="#444466" transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[width / 2, height / 2, length]} rotation={[0, Math.PI, 0]}>
            <planeGeometry args={[width, height]} />
            <meshStandardMaterial color="#444466" transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[width, height / 2, length / 2]} rotation={[0, -Math.PI / 2, 0]}>
            <planeGeometry args={[length, height]} />
            <meshStandardMaterial color="#444466" transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, height / 2, length / 2]} rotation={[0, Math.PI / 2, 0]}>
            <planeGeometry args={[length, height]} />
            <meshStandardMaterial color="#444466" transparent opacity={0.2} side={THREE.DoubleSide} />
          </mesh>
        </>
      )}
    </>
  )
}

function ObjectLabels({ objects, highlighted }: { objects: SceneObject[]; highlighted: string[] }) {
  return (
    <>
      {objects.map(obj => {
        if (!obj.label) return null
        const pos = obj.position || [0, 0, 0]
        const isHighlighted = highlighted.includes(obj.id)
        return (
          <Text
            key={obj.id}
            position={[pos[0], (pos[1] || 0.5) + 0.5, pos[2]]}
            fontSize={0.15}
            color={isHighlighted ? '#FFD700' : '#AAAAAA'}
            anchorX="center"
            anchorY="bottom"
          >
            {obj.label}
          </Text>
        )
      })}
    </>
  )
}

export default function SceneViewer({ layout, objects, highlightedObjects, cameraTarget, onObjectClick }: Props) {
  const safeLayout: SceneLayout = {
    width: layout?.width || 10,
    length: layout?.length || 10,
    height: layout?.height || 3,
    ground_type: layout?.ground_type || 'floor',
    walls: layout?.walls || [],
    lighting: {
      time_of_day: layout?.lighting?.time_of_day || 'day',
      ambient_intensity: layout?.lighting?.ambient_intensity ?? 0.4,
      main_light_position: layout?.lighting?.main_light_position || [5, 8, 5],
    },
  }

  return (
    <div className="w-full h-full rounded-lg overflow-hidden">
      <Canvas
        shadows
        camera={{
          position: [safeLayout.width / 2, safeLayout.height + 4, safeLayout.length + 6],
          fov: 60,
          near: 0.1,
          far: 100,
        }}
      >
        <color attach="background" args={['#1a1a2e']} />
        <fog attach="fog" args={['#1a1a2e', 20, 50]} />

        <ambientLight intensity={safeLayout.lighting.ambient_intensity} />
        <directionalLight
          position={safeLayout.lighting.main_light_position as [number, number, number]}
          intensity={0.8}
          castShadow
        />

        <SceneEnvironment layout={safeLayout} />

        {objects.map(obj => (
          <SceneObject3D
            key={obj.id}
            obj={obj}
            highlighted={highlightedObjects.includes(obj.id)}
            onClick={() => onObjectClick?.(obj.id)}
          />
        ))}

        <ObjectLabels objects={objects} highlighted={highlightedObjects} />

        <CameraController target={cameraTarget || null} />
      </Canvas>
    </div>
  )
}
