/**
 * FamilyTreeSVG
 * Renders an SVG-based family tree with hierarchical node positioning.
 * - Nodes = family members (avatars with initials)
 * - Edges = relationships (PARENT_OF, SPOUSE_OF, SIBLING_OF, CHILD_OF)
 * - Root (family creator) is highlighted with a gold ring
 */

import { useMemo } from 'react'

// ── Constants ─────────────────────────────────────────────
const NODE_R = 24          // avatar radius
const H_GAP = 60           // horizontal gap between siblings
const V_GAP = 110          // vertical gap between generations

const REL_STYLE = {
  PARENT_OF:  { color: '#06b6d4', dash: 'none',   label: 'Parent' },
  CHILD_OF:   { color: '#06b6d4', dash: 'none',   label: 'Child' },
  SPOUSE_OF:  { color: '#ec4899', dash: '6 3',    label: 'Spouse' },
  SIBLING_OF: { color: '#a855f7', dash: '4 2',    label: 'Sibling' },
}

const AVATAR_GRADIENTS = [
  ['#06b6d4', '#3b82f6'],
  ['#8b5cf6', '#d946ef'],
  ['#10b981', '#14b8a6'],
  ['#f43f5e', '#ec4899'],
  ['#f59e0b', '#f97316'],
]

function initials(name, email) {
  if (name) {
    const parts = name.trim().split(/\s+/)
    return parts.length >= 2
      ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      : parts[0][0].toUpperCase()
  }
  return email?.[0]?.toUpperCase() || '?'
}

// ── Layout algorithm ──────────────────────────────────────
function buildLayout(nodes, relationships, rootUserId) {
  if (!nodes || nodes.length === 0) return { positions: {}, width: 300, height: 180 }

  // Index ids
  const ids = nodes.map((n) => n.userId)

  // Build adjacency maps
  const parentOf = {}   // id → [childId]
  const spouseOf = {}   // id → [spouseId]
  const siblingOf = {}  // id → [sibId]

  relationships.forEach(({ source, target, type }) => {
    const link = (map, a, b) => { if (!map[a]) map[a] = []; if (!map[a].includes(b)) map[a].push(b) }

    if (type === 'PARENT_OF') { link(parentOf, source, target) }
    else if (type === 'CHILD_OF') { link(parentOf, target, source) }
    else if (type === 'SPOUSE_OF') { link(spouseOf, source, target); link(spouseOf, target, source) }
    else if (type === 'SIBLING_OF') { link(siblingOf, source, target); link(siblingOf, target, source) }
  })

  // BFS to assign generations
  const generation = {}
  const root = rootUserId && ids.includes(rootUserId) ? rootUserId : ids[0]
  const queue = [{ id: root, gen: 0 }]
  const visited = new Set([root])
  generation[root] = 0

  while (queue.length) {
    const { id, gen } = queue.shift();
    // children → gen + 1
    ;(parentOf[id] || []).forEach((c) => {
      if (!visited.has(c)) { visited.add(c); generation[c] = gen + 1; queue.push({ id: c, gen: gen + 1 }) }
    })
    // spouses & siblings → same gen
    ;[...(spouseOf[id] || []), ...(siblingOf[id] || [])].forEach((s) => {
      if (!visited.has(s)) { visited.add(s); generation[s] = gen; queue.push({ id: s, gen }) }
    })
  }
  // Unvisited nodes → gen 0
  ids.forEach((id) => { if (generation[id] === undefined) generation[id] = 0 })

  // Group by normalised generation (shift so min = 0)
  const minGen = Math.min(...Object.values(generation))
  const rows = {}   // rowIndex → [id]
  ids.forEach((id) => {
    const r = generation[id] - minGen
    if (!rows[r]) rows[r] = []
    rows[r].push(id)
  })

  // Calculate SVG dimensions
  const numRows = Object.keys(rows).length
  const maxCols = Math.max(...Object.values(rows).map((r) => r.length))
  const colUnit = NODE_R * 2 + H_GAP
  const width = Math.max(300, maxCols * colUnit + 60)
  const height = numRows * (NODE_R * 2 + V_GAP) + 60

  // Assign (x, y) to each node
  const positions = {}
  Object.entries(rows).forEach(([rowIdx, rowIds]) => {
    const rowW = rowIds.length * colUnit - H_GAP
    const startX = (width - rowW) / 2
    rowIds.forEach((id, col) => {
      positions[id] = {
        x: startX + col * colUnit + NODE_R,
        y: Number(rowIdx) * (NODE_R * 2 + V_GAP) + NODE_R + 30,
      }
    })
  })

  return { positions, width, height }
}

// ── Component ─────────────────────────────────────────────
export default function FamilyTreeSVG({ members = [], relationships = [], rootUserId }) {
  const nodes = members.map((m) => ({
    userId: m.userId || m.user_id || m.id,
    name: m.name,
    email: m.email,
    role: m.role,
  }))

  const { positions, width, height } = useMemo(
    () => buildLayout(nodes, relationships, rootUserId),
    [nodes, relationships, rootUserId],
  )

  if (nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-white/30">
        <p className="text-sm">No members to display</p>
      </div>
    )
  }

  return (
    <div className="w-full overflow-x-auto">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="mx-auto block"
      >
        <defs>
          {AVATAR_GRADIENTS.map(([c1, c2], i) => (
            <linearGradient key={i} id={`ftg-${i}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={c1} />
              <stop offset="100%" stopColor={c2} />
            </linearGradient>
          ))}
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.4" />
          </filter>
        </defs>

        {/* ── Relationship lines ── */}
        {relationships.map((rel, i) => {
          const p1 = positions[rel.source]
          const p2 = positions[rel.target]
          if (!p1 || !p2) return null
          const style = REL_STYLE[rel.type] || { color: '#ffffff30', dash: 'none', label: rel.type }
          const mx = (p1.x + p2.x) / 2
          const my = (p1.y + p2.y) / 2
          // Curved path
          const dx = p2.x - p1.x
          const dy = p2.y - p1.y
          const cx = mx
          const cy = my - Math.abs(dx) * 0.15  // subtle curve
          const d = `M ${p1.x} ${p1.y} Q ${cx} ${cy} ${p2.x} ${p2.y}`
          return (
            <g key={`rel-${i}`}>
              <path
                d={d}
                fill="none"
                stroke={style.color}
                strokeWidth="1.5"
                strokeOpacity="0.55"
                strokeDasharray={style.dash}
              />
              {/* Relationship label badge */}
              <rect
                x={mx - 18} y={my - 9}
                width={36} height={14}
                rx={7}
                fill={style.color}
                fillOpacity="0.15"
              />
              <text
                x={mx} y={my + 2}
                textAnchor="middle"
                fill={style.color}
                fontSize="8"
                fontWeight="600"
                opacity="0.9"
              >
                {style.label}
              </text>
            </g>
          )
        })}

        {/* ── Avatar nodes ── */}
        {nodes.map((node, i) => {
          const pos = positions[node.userId]
          if (!pos) return null
          const isRoot = node.userId === rootUserId
          const colorIdx = i % AVATAR_GRADIENTS.length
          const label = initials(node.name, node.email)
          const displayName = (node.name?.split(' ')[0] || node.email?.split('@')[0] || '?').slice(0, 10)

          return (
            <g key={node.userId} filter="url(#shadow)">
              {/* Gold ring for family creator */}
              {isRoot && (
                <circle
                  cx={pos.x} cy={pos.y}
                  r={NODE_R + 4}
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="2"
                  opacity="0.7"
                />
              )}
              {/* Avatar circle */}
              <circle
                cx={pos.x} cy={pos.y}
                r={NODE_R}
                fill={`url(#ftg-${colorIdx})`}
              />
              {/* Initials */}
              <text
                x={pos.x} y={pos.y + 5}
                textAnchor="middle"
                fill="white"
                fontSize="12"
                fontWeight="700"
              >
                {label}
              </text>
              {/* Name below avatar */}
              <text
                x={pos.x} y={pos.y + NODE_R + 14}
                textAnchor="middle"
                fill="rgba(255,255,255,0.65)"
                fontSize="10"
              >
                {displayName}
              </text>
              {/* Role badge for admin/root */}
              {node.role === 'admin' && (
                <text
                  x={pos.x} y={pos.y + NODE_R + 26}
                  textAnchor="middle"
                  fill="#f59e0b"
                  fontSize="8"
                  opacity="0.8"
                >
                  admin
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      {relationships.length > 0 && (
        <div className="flex flex-wrap justify-center gap-4 mt-3 px-4">
          {Object.entries(REL_STYLE)
            .filter(([type]) => relationships.some((r) => r.type === type))
            .map(([type, style]) => (
              <div key={type} className="flex items-center gap-1.5">
                <svg width="24" height="6">
                  <line
                    x1="0" y1="3" x2="24" y2="3"
                    stroke={style.color}
                    strokeWidth="2"
                    strokeDasharray={style.dash}
                  />
                </svg>
                <span style={{ color: style.color }} className="text-[10px] font-medium opacity-80">
                  {style.label}
                </span>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
