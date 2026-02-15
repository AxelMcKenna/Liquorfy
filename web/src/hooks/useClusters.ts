import { useMemo } from 'react';
import Supercluster from 'supercluster';
import { Store } from '@/types';

export interface StorePointProperties {
  cluster: false;
  store: Store;
}

export type StorePoint = Supercluster.PointFeature<StorePointProperties>;
export type Cluster = Supercluster.ClusterFeature<Supercluster.AnyProps>;
export type ClusterOrPoint = Cluster | StorePoint;

function isCluster(feature: ClusterOrPoint): feature is Cluster {
  return feature.properties.cluster === true;
}

export { isCluster };

export function useClusters(
  stores: Store[],
  zoom: number,
  bounds: [number, number, number, number] | null,
) {
  const index = useMemo(() => {
    const sc = new Supercluster<StorePointProperties>({
      radius: 60,
      maxZoom: 16,
    });

    const points: StorePoint[] = stores.map((store) => ({
      type: 'Feature',
      properties: { cluster: false, store },
      geometry: {
        type: 'Point',
        coordinates: [store.lon, store.lat],
      },
    }));

    sc.load(points);
    return sc;
  }, [stores]);

  const clusters = useMemo(() => {
    if (!bounds) return [];
    return index.getClusters(bounds, Math.floor(zoom)) as ClusterOrPoint[];
  }, [index, bounds, zoom]);

  return { clusters, index };
}
