import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, Plus, UserPlus, Link2, Trash2, Crown } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import Badge from '@/components/ui/Badge'
import Select from '@/components/ui/Select'
import EmptyState from '@/components/ui/EmptyState'
import FamilyTreeSVG from '@/components/family/FamilyTreeSVG'
import { getInitials } from '@/lib/utils'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export default function FamilyPage() {
  const [families, setFamilies] = useState([])
  const [selectedFamily, setSelectedFamily] = useState(null)
  const [members, setMembers] = useState([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAddMemberModal, setShowAddMemberModal] = useState(false)
  const [showRelationshipModal, setShowRelationshipModal] = useState(false)
  const [familyTree, setFamilyTree] = useState(null)
  const [loading, setLoading] = useState(true)
  const [familyName, setFamilyName] = useState('')
  const [memberEmail, setMemberEmail] = useState('')
  const [memberName, setMemberName] = useState('')
  const [relationship, setRelationship] = useState({ member1: '', member2: '', type: 'PARENT_OF' })

  useEffect(() => {
    loadFamilies()
  }, [])

  const loadFamilies = async () => {
    try {
      const { data } = await api.get('/api/v1/families/me')
      setFamilies(data.families || data || [])
      if (data.families?.length > 0 || data.length > 0) {
        const first = data.families?.[0] || data[0]
        selectFamily(first)
      }
    } catch {
      // graceful fallback
    } finally {
      setLoading(false)
    }
  }

  const selectFamily = async (family) => {
    setSelectedFamily(family)
    const fid = family.familyId || family.family_id || family.id
    try {
      const [membersRes, relsRes] = await Promise.allSettled([
        api.get(`/api/v1/families/${fid}/members`),
        api.get(`/api/v1/families/${fid}/relationships`),
      ])
      if (membersRes.status === 'fulfilled') setMembers(membersRes.value.data.members || membersRes.value.data || [])
      if (relsRes.status === 'fulfilled') setFamilyTree(relsRes.value.data)
    } catch {}
  }

  const createFamily = async () => {
    if (!familyName.trim()) return
    try {
      await api.post('/api/v1/families', { name: familyName })
      toast.success('Family created')
      setShowCreateModal(false)
      setFamilyName('')
      loadFamilies()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create family')
    }
  }

  const addMember = async () => {
    if ((!memberEmail.trim() && !memberName.trim()) || !selectedFamily) return
    try {
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      await api.post(`/api/v1/families/${fid}/members`, {
        email: memberEmail || undefined,
        name: memberName || undefined,
      })
      toast.success('Member added')
      setShowAddMemberModal(false)
      setMemberEmail('')
      setMemberName('')
      loadFamilies()
      selectFamily(selectedFamily)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add member')
    }
  }

  const deleteFamily = async (family, e) => {
    e.stopPropagation()
    if (!window.confirm(`Delete "${family.name}"?`)) return
    try {
      const fid = family.familyId || family.id
      await api.delete(`/api/v1/families/${fid}`)
      toast.success('Family deleted')
      if (selectedFamily?.familyId === fid) {
        setSelectedFamily(null)
        setMembers([])
        setFamilyTree(null)
      }
      loadFamilies()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete family')
    }
  }

  const removeMember = async (memberId) => {
    if (!selectedFamily) return
    try {
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      await api.delete(`/api/v1/families/${fid}/members/${memberId}`)
      toast.success('Member removed')
      selectFamily(selectedFamily)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to remove member')
    }
  }

  const createRelationship = async () => {
    if (!relationship.member1 || !relationship.member2) {
      toast.error('Please select both members')
      return
    }
    if (relationship.member1 === relationship.member2) {
      toast.error('Please select two different members')
      return
    }
    try {
      await api.post(`/api/v1/families/relationships`, {
        user1_id: relationship.member1,
        relationship_type: relationship.type,
        user2_id: relationship.member2,
      })
      toast.success('Relationship created')
      setShowRelationshipModal(false)
      // Refresh tree data
      const fid = selectedFamily.familyId || selectedFamily.family_id || selectedFamily.id
      const relsRes = await api.get(`/api/v1/families/${fid}/relationships`)
      setFamilyTree(relsRes.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create relationship')
    }
  }

  const avatarColors = [
    'from-cyan-500 to-blue-500',
    'from-violet-500 to-fuchsia-500',
    'from-emerald-500 to-teal-500',
    'from-rose-500 to-pink-500',
    'from-amber-500 to-orange-500',
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Family Management</h2>
          <p className="text-sm text-white/40">Manage your family groups and relationships</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} size="sm">
          <Plus className="w-4 h-4" />
          Create Family
        </Button>
      </div>

      {/* Family Cards */}
      {families.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {families.map((family, i) => (
            <motion.div
              key={family.familyId || family.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard
                className={`cursor-pointer ${selectedFamily?.familyId === family.familyId ? 'glow-cyan border-cyan-500/30' : ''}`}
                onClick={() => selectFamily(family)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-cyan-400" />
                    <h3 className="font-semibold text-white">{family.name}</h3>
                  </div>
                  <button
                    onClick={(e) => deleteFamily(family, e)}
                    className="p-1.5 rounded-lg hover:bg-rose-500/10 text-white/20 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-xs text-white/40">
                  {family.member_count ?? 0} members
                </p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      ) : !loading ? (
        <EmptyState
          icon={Users}
          title="No families yet"
          description="Create a family group to manage health data together"
          action={
            <Button onClick={() => setShowCreateModal(true)} size="sm">
              <Plus className="w-4 h-4" /> Create Family
            </Button>
          }
        />
      ) : null}

      {/* Selected Family Details */}
      {selectedFamily && (
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Crown className="w-4 h-4 text-amber-400" />
              {selectedFamily.name} - Members
            </h3>
            <div className="flex gap-2">
              <Button onClick={() => setShowAddMemberModal(true)} variant="ghost" size="sm">
                <UserPlus className="w-4 h-4" /> Add
              </Button>
              <Button onClick={() => {
                const getId = m => m.userId || m.user_id || m.id || ''
                setRelationship({
                  member1: members[0] ? getId(members[0]) : '',
                  member2: members[1] ? getId(members[1]) : '',
                  type: 'PARENT_OF',
                })
                setShowRelationshipModal(true)
              }} variant="ghost" size="sm">
                <Link2 className="w-4 h-4" /> Relationship
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            {members.map((member, i) => (
              <motion.div
                key={member.id || i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 glass rounded-xl p-3"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${avatarColors[i % avatarColors.length]} flex items-center justify-center text-sm font-bold text-white`}>
                  {getInitials(member.name?.split(' ')[0], member.name?.split(' ')[1])}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {member.name || member.email || 'Unknown'}
                  </p>
                  <p className="text-xs text-white/40">{member.email}</p>
                </div>
                {member.role && <Badge color="violet">{member.role}</Badge>}
                <button
                  onClick={() => removeMember(member.userId || member.user_id || member.id)}
                  className="p-1.5 rounded-lg hover:bg-rose-500/10 text-white/30 hover:text-rose-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </div>

          {/* Family Tree Visualization */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-white/60">Family Tree</h4>
              {familyTree?.relationships?.length === 0 && (
                <p className="text-[11px] text-white/30">Add relationships to see connections</p>
              )}
            </div>
            <div className="glass rounded-xl p-4">
              <FamilyTreeSVG
                members={members}
                relationships={familyTree?.relationships || []}
                rootUserId={selectedFamily?.createdBy}
              />
            </div>
          </div>
        </GlassCard>
      )}

      {/* Create Family Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Family">
        <div className="space-y-4">
          <Input
            label="Family Name"
            placeholder="e.g., Smith Family"
            value={familyName}
            onChange={(e) => setFamilyName(e.target.value)}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={createFamily} className="flex-1">Create</Button>
          </div>
        </div>
      </Modal>

      {/* Add Member Modal */}
      <Modal isOpen={showAddMemberModal} onClose={() => setShowAddMemberModal(false)} title="Add Member">
        <div className="space-y-4">
          <Input
            label="Member Name"
            placeholder="e.g., Ahmed Khan"
            value={memberName}
            onChange={(e) => setMemberName(e.target.value)}
          />
          <Input
            label="Member Email (optional)"
            type="email"
            placeholder="member@example.com"
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowAddMemberModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={addMember} className="flex-1">Add Member</Button>
          </div>
        </div>
      </Modal>

      {/* Relationship Modal */}
      <Modal isOpen={showRelationshipModal} onClose={() => setShowRelationshipModal(false)} title="Create Relationship">
        <div className="space-y-4">
          <Select
            label="Member 1"
            options={members.map(m => ({ value: m.userId || m.user_id || m.id, label: m.name || m.email || 'Unknown' }))}
            value={relationship.member1}
            onChange={(e) => setRelationship(prev => ({ ...prev, member1: e.target.value }))}
          />
          <Select
            label="Relationship Type"
            options={[
              { value: 'PARENT_OF', label: 'Parent of' },
              { value: 'CHILD_OF', label: 'Child of' },
              { value: 'SPOUSE_OF', label: 'Spouse of' },
              { value: 'SIBLING_OF', label: 'Sibling of' },
            ]}
            value={relationship.type}
            onChange={(e) => setRelationship(prev => ({ ...prev, type: e.target.value }))}
          />
          <Select
            label="Member 2"
            options={members.map(m => ({ value: m.userId || m.user_id || m.id, label: m.name || m.email || 'Unknown' }))}
            value={relationship.member2}
            onChange={(e) => setRelationship(prev => ({ ...prev, member2: e.target.value }))}
          />
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowRelationshipModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={createRelationship} className="flex-1">Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
