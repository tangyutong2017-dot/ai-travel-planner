export type ItineraryItem = {
  id: string;
  startTime: string;
  endTime: string;
  title: string;
  type: string;
  durationLabel: string;
  cost: number;
  reason?: string;
  transitFromPrev?: string;
  address?: string;
  location?: { lat: number; lng: number };
  poiId?: string;
  source?: string;
  imageUrl?: string;
  mealType?: string;
  countsAsMajorPlace?: boolean;
};

export type DayPlan = {
  day: number;
  date: string;
  title: string;
  generationStatus?: "pending" | "generating" | "preview" | "finalized" | "failed";
  weather: { icon: string; desc: string; range: string; tip?: string };
  mealSuggestions?: {
    breakfast: { time: string; area: string; suggestion: string; nearbyPlace?: string; reason?: string };
    lunch: { time: string; area: string; suggestion: string; nearbyPlace?: string; reason?: string };
    dinner: { time: string; area: string; suggestion: string; nearbyPlace?: string; reason?: string };
  };
  route: { distanceKm: number; walkKm: number; transitKm: number; durationLabel: string };
  items: ItineraryItem[];
};

export type Itinerary = {
  tripId: string;
  destination: string;
  title: string;
  dateRange: string;
  travelers: number;
  interests: string[];
  days: DayPlan[];
};
