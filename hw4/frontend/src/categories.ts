// Shop categories. `value` is the backend category key (the same matching the chatbot's search uses).
export const CATEGORIES = [
  { value: 'hoodie', label: 'Hoodies', feature: 'basic-hoodie-big-yale' },
  { value: 'crewneck', label: 'Crewnecks', feature: 'district-vit-crewneck-vintage-standing-bulldog' },
  { value: 't-shirt', label: 'T-Shirts', feature: 'boola-boola-t-shirt' },
  { value: 'quarter-zip', label: 'Quarter-Zips', feature: 'benjamin-franklin-1-4-zip' },
  { value: 'jacket', label: 'Jackets & Fleece', feature: 'benjamin-franklin-fleece-jacket' },
  { value: 'long-sleeve', label: 'Long Sleeves', feature: '' },
]

// Same order as backend tools.category_of ("short-sleeve crew-neck t-shirt" is a t-shirt).
const CATEGORY_KEYS = ['hood', 'quarter-zip', 't-shirt', 'jacket', 'long-sleeve', 'crewneck']

export function categoryOf(garmentType: string): (typeof CATEGORIES)[number] | undefined {
  const gt = garmentType.toLowerCase()
  const key = CATEGORY_KEYS.find((k) => gt.includes(k))
  return CATEGORIES.find((c) => (key === 'hood' ? c.value === 'hoodie' : c.value === key))
}

// Approximate swatch colors for the catalogue's color names.
const SWATCHES: [string, string][] = [
  ['navy', '#1d2a48'],
  ['charcoal', '#4a4f57'],
  ['heather', '#a3a7ad'],
  ['gray', '#9ca3af'],
  ['grey', '#9ca3af'],
  ['white', '#ffffff'],
  ['cream', '#f1e9d6'],
  ['oatmeal', '#e8dfcc'],
  ['black', '#16181c'],
  ['red', '#b42318'],
  ['maroon', '#6b1d2a'],
  ['green', '#2f6b3a'],
  ['gold', '#c9a227'],
  ['yellow', '#e3b505'],
  ['orange', '#d9692b'],
  ['peach', '#f2a48b'],
  ['coral', '#f08a73'],
  ['pink', '#f0a3c0'],
  ['blue', '#286dc0'],
]

export function swatchFor(color: string): string {
  const c = color.toLowerCase()
  return SWATCHES.find(([name]) => c.includes(name))?.[1] ?? '#c9c4b8'
}
