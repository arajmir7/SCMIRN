import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';

export type RiskHorizon = '7d' | '30d' | '90d';

export interface RiskRadarNode {
  node_id: string;
  district: string;
  risk_type: string;
  coordinates: {
    lat: number;
    lng: number;
    altitude_m: number;
  };
  forecasts: {
    '7d': number;
    '30d': number;
    '90d': number;
  };
  priority: string;
}

interface RiskRadarGlobeProps {
  nodes: RiskRadarNode[];
  height?: number;
}

function latLngToCartesian(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

function colorForScore(score: number): number {
  if (score >= 75) {
    return 0xef4444;
  }
  if (score >= 55) {
    return 0xf59e0b;
  }
  return 0x22c55e;
}

function normalizeNodes(nodes: RiskRadarNode[]): RiskRadarNode[] {
  return nodes
    .filter(
      (node) =>
        Number.isFinite(node?.coordinates?.lat) &&
        Number.isFinite(node?.coordinates?.lng) &&
        Number.isFinite(node?.forecasts?.['7d']) &&
        Number.isFinite(node?.forecasts?.['30d']) &&
        Number.isFinite(node?.forecasts?.['90d'])
    )
    .slice(0, 300);
}

export function RiskRadarGlobe({ nodes, height = 340 }: RiskRadarGlobeProps) {
  const [horizon, setHorizon] = useState<RiskHorizon>('30d');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const mountRef = useRef<HTMLDivElement | null>(null);

  const safeNodes = useMemo(() => normalizeNodes(nodes), [nodes]);

  const rankedNodes = useMemo(
    () =>
      [...safeNodes].sort((a, b) => {
        const scoreA = a.forecasts[horizon];
        const scoreB = b.forecasts[horizon];
        return scoreB - scoreA;
      }),
    [safeNodes, horizon]
  );

  useEffect(() => {
    if (safeNodes.length === 0) {
      setSelectedNodeId(null);
      return;
    }
    if (!selectedNodeId || !safeNodes.some((node) => node.node_id === selectedNodeId)) {
      setSelectedNodeId(safeNodes[0].node_id);
    }
  }, [safeNodes, selectedNodeId]);

  const selectedNode = useMemo(
    () => safeNodes.find((node) => node.node_id === selectedNodeId) ?? rankedNodes[0] ?? null,
    [safeNodes, selectedNodeId, rankedNodes]
  );

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount || safeNodes.length === 0) {
      return;
    }

    mount.replaceChildren();
    const width = Math.max(280, mount.clientWidth || 280);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);

    const camera = new THREE.PerspectiveCamera(46, width / height, 0.1, 120);
    camera.position.set(0, 0, 3.1);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    mount.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0x60a5fa, 0.95);
    keyLight.position.set(3.2, 2.3, 2.7);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x22d3ee, 0.45);
    fillLight.position.set(-3.2, -1.5, -2.2);
    scene.add(fillLight);

    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    const sphereGeometry = new THREE.SphereGeometry(1, 64, 64);
    const sphereMaterial = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      metalness: 0.12,
      roughness: 0.88,
    });
    const earth = new THREE.Mesh(sphereGeometry, sphereMaterial);
    globeGroup.add(earth);

    const wireMaterial = new THREE.LineBasicMaterial({
      color: 0x334155,
      transparent: true,
      opacity: 0.35,
    });
    const wireSourceGeometry = new THREE.SphereGeometry(1.002, 20, 20);
    const wireGeometry = new THREE.WireframeGeometry(wireSourceGeometry);
    wireSourceGeometry.dispose();
    const wireframe = new THREE.LineSegments(wireGeometry, wireMaterial);
    globeGroup.add(wireframe);

    const atmosphereMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide,
    });
    const atmosphere = new THREE.Mesh(new THREE.SphereGeometry(1.08, 48, 48), atmosphereMaterial);
    globeGroup.add(atmosphere);

    const markersGroup = new THREE.Group();
    globeGroup.add(markersGroup);
    const stemsGroup = new THREE.Group();
    globeGroup.add(stemsGroup);

    const markerGeometry = new THREE.SphereGeometry(0.016, 12, 12);
    const markerMeshes: THREE.Mesh[] = [];

    safeNodes.forEach((node) => {
      const score = node.forecasts[horizon];
      const altitude = Math.min(0.2, Math.max(0.02, (node.coordinates.altitude_m || 0) / 14000));
      const markerRadius = 1.02 + altitude;
      const markerPosition = latLngToCartesian(node.coordinates.lat, node.coordinates.lng, markerRadius);
      const stemBase = latLngToCartesian(node.coordinates.lat, node.coordinates.lng, 1.0);
      const color = colorForScore(score);

      const markerMaterial = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.25,
      });
      const marker = new THREE.Mesh(markerGeometry, markerMaterial);
      marker.position.copy(markerPosition);
      marker.userData = { nodeId: node.node_id };
      if (selectedNodeId === node.node_id) {
        marker.scale.setScalar(1.6);
      }
      markerMeshes.push(marker);
      markersGroup.add(marker);

      const stemGeometry = new THREE.BufferGeometry().setFromPoints([stemBase, markerPosition]);
      const stemMaterial = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.42,
      });
      stemsGroup.add(new THREE.Line(stemGeometry, stemMaterial));
    });

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2(10, 10);

    const handleMove = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const intersections = raycaster.intersectObjects(markerMeshes, false);
      renderer.domElement.style.cursor = intersections.length > 0 ? 'pointer' : 'grab';
    };

    const handleClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const intersections = raycaster.intersectObjects(markerMeshes, false);
      if (intersections.length > 0) {
        const nodeId = intersections[0].object.userData?.nodeId as string | undefined;
        if (nodeId) {
          setSelectedNodeId(nodeId);
        }
      }
    };

    renderer.domElement.addEventListener('mousemove', handleMove);
    renderer.domElement.addEventListener('click', handleClick);
    renderer.domElement.style.cursor = 'grab';

    let frame = 0;
    const renderFrame = () => {
      globeGroup.rotation.y += 0.0016;
      renderer.render(scene, camera);
      frame = window.requestAnimationFrame(renderFrame);
    };
    renderFrame();

    const handleResize = () => {
      const nextWidth = Math.max(280, mount.clientWidth || 280);
      camera.aspect = nextWidth / height;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, height);
    };
    window.addEventListener('resize', handleResize);
    const resizeObserver = typeof ResizeObserver === 'undefined'
      ? null
      : new ResizeObserver(handleResize);
    resizeObserver?.observe(mount);

    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener('resize', handleResize);
      resizeObserver?.disconnect();
      renderer.domElement.removeEventListener('mousemove', handleMove);
      renderer.domElement.removeEventListener('click', handleClick);
      scene.traverse((object) => {
        const mesh = object as THREE.Mesh;
        if (mesh.geometry) {
          mesh.geometry.dispose();
        }
        const material = mesh.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(material)) {
          material.forEach((item) => item.dispose());
        } else if (material) {
          material.dispose();
        }
      });
      renderer.dispose();
      mount.replaceChildren();
    };
  }, [safeNodes, horizon, selectedNodeId, height]);

  return (
    <div className="risk-globe-shell">
      <div className="inline-actions">
        <label className="risk-globe-label" htmlFor="risk-horizon">
          Forecast Horizon
        </label>
        <select
          id="risk-horizon"
          className="select risk-horizon-select"
          value={horizon}
          onChange={(event) => setHorizon(event.target.value as RiskHorizon)}
        >
          <option value="7d">7 Days</option>
          <option value="30d">30 Days</option>
          <option value="90d">90 Days</option>
        </select>
      </div>

      <div ref={mountRef} className="risk-globe-canvas" aria-label="3D predictive risk radar globe" />

      <div className="risk-globe-legend">
        <span><i className="risk-dot risk-dot-low" /> Low</span>
        <span><i className="risk-dot risk-dot-medium" /> Medium</span>
        <span><i className="risk-dot risk-dot-high" /> High</span>
      </div>

      {selectedNode ? (
        <div className="risk-globe-meta">
          <strong>{selectedNode.district} - {selectedNode.risk_type}</strong>
          <span>7d: {selectedNode.forecasts['7d']} | 30d: {selectedNode.forecasts['30d']} | 90d: {selectedNode.forecasts['90d']}</span>
          <span>Priority: {selectedNode.priority}</span>
        </div>
      ) : null}
    </div>
  );
}

export default RiskRadarGlobe;
