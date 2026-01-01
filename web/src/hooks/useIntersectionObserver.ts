import { useEffect, useRef, RefObject } from 'react';

interface UseIntersectionObserverOptions {
  onIntersect: () => void;
  enabled?: boolean;
  rootMargin?: string;
  threshold?: number;
}

export const useIntersectionObserver = ({
  onIntersect,
  enabled = true,
  rootMargin = '200px',
  threshold = 0.1,
}: UseIntersectionObserverOptions): RefObject<HTMLDivElement> => {
  const targetRef = useRef<HTMLDivElement>(null);
  const isIntersectingRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    const target = targetRef.current;
    if (!target) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        // Only trigger if we're entering the viewport (not leaving)
        // and we haven't already triggered
        if (entry.isIntersecting && !isIntersectingRef.current) {
          isIntersectingRef.current = true;
          onIntersect();
        } else if (!entry.isIntersecting) {
          isIntersectingRef.current = false;
        }
      },
      {
        rootMargin,
        threshold,
      }
    );

    observer.observe(target);

    return () => {
      if (target) {
        observer.unobserve(target);
      }
    };
  }, [enabled, onIntersect, rootMargin, threshold]);

  return targetRef;
};
