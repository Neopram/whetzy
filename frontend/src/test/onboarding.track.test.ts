import { describe, expect, it } from 'vitest'
import { _placementTrack } from '../pages/OnboardingScreen'

describe('_placementTrack', () => {
  it('goal 0 (learn fundamentals) → track01', () => {
    expect(_placementTrack(0, null)).toBe('track01')
  })

  it('goal 1 (get a job) → track04', () => {
    expect(_placementTrack(1, null)).toBe('track04')
  })

  it('goal 2 (advance career) → track04', () => {
    expect(_placementTrack(2, null)).toBe('track04')
  })

  it('goal 3 + cert elegida → el track de la cert', () => {
    expect(_placementTrack(3, 'track08')).toBe('track08')
    expect(_placementTrack(3, 'track44')).toBe('track44')
  })

  it('goal 3 sin cert → track01 como fallback', () => {
    expect(_placementTrack(3, null)).toBe('track01')
  })
})
