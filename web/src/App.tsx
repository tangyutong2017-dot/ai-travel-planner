import { useEffect, useMemo, useState } from "react";
import { TopNav, LeftSidebar } from "./components/layout/AppLayout";
import { PageMyTrips } from "./features/trips/TripsPage";
import { WizardOverlay } from "./features/wizard/WizardOverlay";
import { ModalAttraction, PageWorkspace } from "./features/workspace/WorkspacePage";
import { PageOutput } from "./features/output/OutputPage";
import type { ItineraryItem } from "./types/itinerary";
import { getTrips } from "./api/trips";
import type { Trip } from "./types/trip";

type Route =
  { page: "trips" } | { page: "newTrip" } | { page: "workspace"; tripId: string } | { page: "output"; tripId: string };

const FALLBACK_RECENT_TRIPS: Trip[] = [];

function tripUpdatedTime(trip: Trip) {
  return trip.updatedAt ? Date.parse(trip.updatedAt) || 0 : 0;
}

function pickDefaultWorkspaceTripId(trips: Trip[], rememberedTripId: string) {
  const rememberedTrip = trips.find((trip) => trip.id === rememberedTripId);
  if (rememberedTrip) return rememberedTrip.id;

  const plannedTrips = trips.filter((trip) => trip.status === "计划中");
  const sortedPlannedTrips = [...plannedTrips].sort((a, b) => tripUpdatedTime(b) - tripUpdatedTime(a));
  return sortedPlannedTrips[0]?.id ?? trips[0]?.id ?? "";
}

function parseRoute(pathname: string): Route {
  const parts = pathname.split("/").filter(Boolean);

  if (parts[0] !== "trips") {
    return { page: "trips" };
  }

  if (parts[1] === "new") {
    return { page: "newTrip" };
  }

  if (parts[1] && parts[2] === "workspace") {
    return { page: "workspace", tripId: parts[1] };
  }

  if (parts[1] && parts[2] === "output") {
    return { page: "output", tripId: parts[1] };
  }

  return { page: "trips" };
}

function routePath(route: Route) {
  if (route.page === "trips") return "/trips";
  if (route.page === "newTrip") return "/trips/new";
  if (route.page === "workspace") return `/trips/${route.tripId}/workspace`;
  return `/trips/${route.tripId}/output`;
}

function currentNav(route: Route) {
  if (route.page === "workspace") return "workspace";
  if (route.page === "output") return "output";
  return "mytrips";
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.pathname));
  const [selectedAttraction, setSelectedAttraction] = useState<ItineraryItem | null>(null);
  const [recentTrips, setRecentTrips] = useState<Trip[]>(FALLBACK_RECENT_TRIPS);
  const [recentReloadKey, setRecentReloadKey] = useState(0);
  const [lastWorkspaceTripId, setLastWorkspaceTripId] = useState(
    () => window.localStorage.getItem("travel-planner:last-workspace-trip") ?? "",
  );

  useEffect(() => {
    if (window.location.pathname === "/") {
      window.history.replaceState(null, "", "/trips");
      setRoute({ page: "trips" });
    }

    const handlePopState = () => {
      setRoute(parseRoute(window.location.pathname));
      setSelectedAttraction(null);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const refreshRecentTrips = () => setRecentReloadKey((key) => key + 1);

  useEffect(() => {
    let ignore = false;

    async function loadRecentTrips() {
      try {
        const response = await getTrips({ sort: "updatedAt_desc" });
        if (!ignore) {
          setRecentTrips(response.items);
        }
      } catch {
        if (!ignore) {
          setRecentTrips(FALLBACK_RECENT_TRIPS);
        }
      }
    }

    loadRecentTrips();

    return () => {
      ignore = true;
    };
  }, [recentReloadKey]);

  const activeTripId = useMemo(() => {
    if (route.page === "workspace" || route.page === "output") return route.tripId;
    return pickDefaultWorkspaceTripId(recentTrips, lastWorkspaceTripId);
  }, [lastWorkspaceTripId, recentTrips, route]);

  const activeTrip = useMemo(() => recentTrips.find((trip) => trip.id === activeTripId), [activeTripId, recentTrips]);

  const topNavTitle = useMemo(() => {
    if (route.page === "trips") return "我的行程";
    if (route.page === "newTrip") return "创建新行程";
    if (route.page === "workspace") return `工作区 / ${activeTrip?.name ?? activeTripId}`;
    return `输出预览 / ${activeTrip?.name ?? activeTripId}`;
  }, [activeTrip?.name, activeTripId, route.page]);

  const navigateTo = (nextRoute: Route) => {
    if (nextRoute.page === "workspace") {
      setLastWorkspaceTripId(nextRoute.tripId);
      window.localStorage.setItem("travel-planner:last-workspace-trip", nextRoute.tripId);
    }

    window.history.pushState(null, "", routePath(nextRoute));
    setRoute(nextRoute);
    setSelectedAttraction(null);
  };

  const defaultWorkspaceTripId = useMemo(() => {
    return pickDefaultWorkspaceTripId(recentTrips, lastWorkspaceTripId);
  }, [lastWorkspaceTripId, recentTrips]);

  useEffect(() => {
    if (route.page !== "workspace" && route.page !== "output") return;
    if (recentTrips.length === 0) return;
    if (recentTrips.some((trip) => trip.id === route.tripId)) return;

    if (defaultWorkspaceTripId) {
      navigateTo({ page: route.page, tripId: defaultWorkspaceTripId });
    }
  }, [defaultWorkspaceTripId, recentTrips, route]);

  const navigateFromSidebar = (id: string) => {
    const targetTripId = activeTrip?.id ?? defaultWorkspaceTripId;

    if (id === "mytrips") navigateTo({ page: "trips" });
    if (id === "workspace" && targetTripId) navigateTo({ page: "workspace", tripId: targetTripId });
    if (id === "output" && targetTripId) navigateTo({ page: "output", tripId: targetTripId });
  };

  const openWizard = () => navigateTo({ page: "newTrip" });
  const closeWizard = () => navigateTo({ page: "trips" });
  const finishWizard = (tripId: string) => {
    refreshRecentTrips();
    navigateTo({ page: "workspace", tripId });
  };

  return (
    <div
      className="flex flex-col h-screen bg-gray-50 relative overflow-hidden"
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      <TopNav title={topNavTitle} />

      <div className="flex-1 flex overflow-hidden relative">
        <LeftSidebar
          current={currentNav(route)}
          onNavigate={navigateFromSidebar}
          onCreateTrip={openWizard}
          recentTrips={recentTrips}
          onOpenTrip={(tripId) => navigateTo({ page: "workspace", tripId })}
        />

        <div className="flex-1 flex overflow-hidden relative">
          {(route.page === "trips" || route.page === "newTrip") && (
            <PageMyTrips
              onCreate={openWizard}
              onOpenTrip={(tripId) => navigateTo({ page: "workspace", tripId })}
              onTripsChanged={refreshRecentTrips}
            />
          )}
          {route.page === "workspace" && (
            <PageWorkspace
              tripId={route.tripId}
              onOpenModal={setSelectedAttraction}
              onOutput={() => navigateTo({ page: "output", tripId: route.tripId })}
              onTripChanged={refreshRecentTrips}
            />
          )}
          {route.page === "output" && (
            <PageOutput tripId={route.tripId} onBack={() => navigateTo({ page: "workspace", tripId: route.tripId })} />
          )}

          {selectedAttraction && (
            <ModalAttraction item={selectedAttraction} onClose={() => setSelectedAttraction(null)} />
          )}

          {route.page === "newTrip" && <WizardOverlay onClose={closeWizard} onDone={finishWizard} />}
        </div>
      </div>
    </div>
  );
}
