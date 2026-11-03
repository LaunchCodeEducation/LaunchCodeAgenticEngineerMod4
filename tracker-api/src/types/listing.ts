export type Listing = {
  id: string
  source: string
  listingUrl: string
  title: string | null
  price: string | null
  location: string | null
  imageUrl: string | null
  savedSearchId: string | null
  seenAt: Date
}
