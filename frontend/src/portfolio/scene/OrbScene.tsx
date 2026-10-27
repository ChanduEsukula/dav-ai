import { useEffect, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Group, MathUtils, PMREMGenerator } from 'three'
import type { ExperienceMode } from '../../components/experienceState'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'

// A thin Fresnel surface restores the edge reflection of clear glass without a
// full-screen bloom/postprocessing pass. The interior uses physical transmission.
const glassVertex = `
  varying vec3 vNormal;
  varying vec3 vEye;
  void main() {
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    vNormal = normalize(normalMatrix * normal);
    vEye = -viewPosition.xyz;
    gl_Position = projectionMatrix * viewPosition;
  }
`
const glassFragment = `
  varying vec3 vNormal;
  varying vec3 vEye;
  void main() {
    vec3 n = normalize(vNormal);
    float rim = pow(1.0 - abs(dot(n, normalize(vEye))), 2.8);
    float highlight = pow(max(0.0, dot(n, normalize(vec3(-0.6, 0.8, 0.5)))), 32.0);
    vec3 tint = mix(vec3(0.22, 0.68, 0.78), vec3(0.84, 1.0, 0.98), smoothstep(-0.6, 0.8, n.y));
    gl_FragColor = vec4(tint, rim * 0.62 + highlight * 0.16);
  }
`

function RenderBudget() {
  const width = useThree(state => state.size.width)
  const setDpr = useThree(state => state.setDpr)
  useEffect(() => { setDpr(width < 480 ? 1 : [1, 1.5]) }, [width, setDpr])
  return null
}

function StudioEnvironment() {
  const { gl, scene } = useThree()
  useEffect(() => {
    const generator = new PMREMGenerator(gl)
    const room = new RoomEnvironment()
    const texture = generator.fromScene(room, 0.04)
    // Three.js owns this imperative scene; React does not render its properties.
    // eslint-disable-next-line react-hooks/immutability
    scene.environment = texture.texture
    room.dispose()
    generator.dispose()
    return () => {
      scene.environment = null
      texture.dispose()
    }
  }, [gl, scene])
  return null
}

function FloatingGlass({ pro }: { pro: boolean }) {
  const orb = useRef<Group>(null)
  const capsule = useRef<Group>(null)
  const rig = useRef<Group>(null)
  useFrame(({ clock, pointer }, delta) => {
    const time = clock.getElapsedTime()
    if (rig.current) {
      rig.current.rotation.y = MathUtils.damp(rig.current.rotation.y, pointer.x * .09, 3, delta)
      rig.current.rotation.x = MathUtils.damp(rig.current.rotation.x, -pointer.y * .06, 3, delta)
      rig.current.position.y = Math.sin(time * .35) * .07
    }
    if (orb.current) orb.current.rotation.y = time * .045
    if (capsule.current) {
      capsule.current.rotation.z = .52 + Math.sin(time * .3) * .035
      capsule.current.rotation.y = Math.sin(time * .22) * .16
      capsule.current.position.y = Math.sin(time * .47) * .045
    }
  })
  return <group ref={rig}>
    <group ref={capsule} rotation={[.12, 0, .52]}>
      <mesh position={[0, -.4, 0]}>
        <cylinderGeometry args={[.39, .39, .8, 48]} />
        <meshPhysicalMaterial color="#d6f5f2" metalness={.18} roughness={.19} clearcoat={1} />
      </mesh>
      <mesh position={[0, -.8, 0]} rotation={[Math.PI, 0, 0]}>
        <sphereGeometry args={[.39, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshPhysicalMaterial color="#d6f5f2" metalness={.18} roughness={.19} clearcoat={1} />
      </mesh>
      <mesh position={[0, .4, 0]}>
        <cylinderGeometry args={[.397, .397, .8, 48]} />
        <meshPhysicalMaterial color={pro ? '#7253dd' : '#138f9e'} metalness={.38} roughness={.14} clearcoat={1} />
      </mesh>
      <mesh position={[0, .8, 0]}>
        <sphereGeometry args={[.397, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshPhysicalMaterial color={pro ? '#7253dd' : '#138f9e'} metalness={.38} roughness={.14} clearcoat={1} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[.396, .009, 8, 64]} />
        <meshStandardMaterial color="#b6f8ed" metalness={.6} roughness={.18} />
      </mesh>
    </group>
    <group ref={orb} rotation={[.18, 0, -.35]}>
      <mesh scale={[1, 1.08, 1]}>
        <sphereGeometry args={[1.65, 64, 48]} />
        <meshPhysicalMaterial color={pro ? '#d3c4ff' : '#c4f6ff'} transmission={.98} transparent opacity={.24} thickness={.1} ior={1.25}
          roughness={.045} metalness={0} clearcoat={.6} clearcoatRoughness={.08} envMapIntensity={.8} />
      </mesh>
      <mesh scale={[1.003, 1.08324, 1.003]} renderOrder={2}>
        <sphereGeometry args={[1.65, 64, 48]} />
        <shaderMaterial vertexShader={glassVertex} fragmentShader={glassFragment} transparent depthWrite={false} />
      </mesh>
      <mesh rotation={[.48, .65, .3]}>
        <torusGeometry args={[1.88, .008, 8, 128]} />
        <meshStandardMaterial color="#7acee1" metalness={.7} roughness={.2} emissive="#4eabbd" emissiveIntensity={.18} />
      </mesh>
      <mesh rotation={[1.07, -.4, -.8]}>
        <torusGeometry args={[1.93, .006, 8, 128]} />
        <meshStandardMaterial color="#c0d9ca" metalness={.65} roughness={.22} />
      </mesh>
    </group>
  </group>
}

export default function OrbScene({ active, onReady, onFailure, mode }: {
  mode: ExperienceMode; active: boolean; onReady: () => void; onFailure: () => void
}) {
  return <Canvas camera={{ position: [0, 0, 6.7], fov: 39 }} dpr={[1, 1.5]}
    frameloop={active ? 'always' : 'never'} gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}
    onCreated={({ gl }) => {
      gl.domElement.addEventListener('webglcontextlost', onFailure, { once: true })
      onReady()
    }}>
    <RenderBudget />
    <StudioEnvironment />
    <ambientLight intensity={.5} />
    <directionalLight position={[3, 5, 5]} color="#d9ffff" intensity={3} />
    <pointLight position={[-3, 1, 2]} color={mode === 'research_pro' ? '#8d70ff' : '#2bdbe1'} intensity={18} />
    <pointLight position={[3, -2, 2]} color={mode === 'research_pro' ? '#a4b6ff' : '#ffdfbb'} intensity={9} />
    <FloatingGlass pro={mode === 'research_pro'} />
  </Canvas>
}
