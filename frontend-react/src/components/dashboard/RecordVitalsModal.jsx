import { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import Modal from '@/components/ui/Modal'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import api from '@/lib/axios'

export default function RecordVitalsModal({ isOpen, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, reset } = useForm()

  const onSubmit = async (data) => {
    setLoading(true)
    const today = new Date().toISOString().split('T')[0]
    try {
      const requests = []

      // Blood pressure (systolic + diastolic + optional heart rate)
      if (data.systolic && data.diastolic) {
        requests.push(api.post('/api/v1/vitals/blood-pressure', {
          systolic: parseFloat(data.systolic),
          diastolic: parseFloat(data.diastolic),
          heart_rate: data.heart_rate ? parseFloat(data.heart_rate) : undefined,
          date: today,
        }))
      }

      // Temperature
      if (data.temperature) {
        requests.push(api.post('/api/v1/vitals/record', {
          vital_type: 'temperature',
          value: parseFloat(data.temperature),
          unit: '°F',
          date: today,
        }))
      }

      // Weight
      if (data.weight) {
        requests.push(api.post('/api/v1/vitals/record', {
          vital_type: 'weight',
          value: parseFloat(data.weight),
          unit: 'lbs',
          date: today,
        }))
      }

      await Promise.all(requests)
      toast.success('Vitals recorded successfully')
      reset()
      onSuccess ? onSuccess() : onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record vitals')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record Vitals" size="md">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Systolic BP"
            type="number"
            placeholder="120"
            {...register('systolic', { required: true })}
          />
          <Input
            label="Diastolic BP"
            type="number"
            placeholder="80"
            {...register('diastolic', { required: true })}
          />
        </div>
        <Input
          label="Heart Rate (BPM)"
          type="number"
          placeholder="72"
          {...register('heart_rate', { required: true })}
        />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Temperature (F)"
            type="number"
            step="0.1"
            placeholder="98.6"
            {...register('temperature')}
          />
          <Input
            label="Weight (lbs)"
            type="number"
            step="0.1"
            placeholder="150"
            {...register('weight')}
          />
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} className="flex-1">Cancel</Button>
          <Button type="submit" loading={loading} className="flex-1">Save Vitals</Button>
        </div>
      </form>
    </Modal>
  )
}
