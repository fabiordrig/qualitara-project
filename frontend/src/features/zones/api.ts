import axios from 'axios'
import type { ZoneCount } from './types'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function fetchZoneCounts(): Promise<ZoneCount[]> {
  const response = await api.get<ZoneCount[]>('/zones/counts')
  return response.data
}
