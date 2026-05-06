(define
  (problem blocks_words)
  (:domain blocks)
  (:objects)
  (:init (HANDEMPTY) (CLEAR T) (ONTABLE T) (CLEAR U) (ONTABLE U) (CLEAR R) (ONTABLE R) (CLEAR K) (ONTABLE K) (CLEAR C) (ONTABLE C) (CLEAR S) (ON S A) (ON A H) (ONTABLE H) (obs_0))
  (:goal (and (CLEAR S) (ONTABLE R) (ON S T) (ON T A) (ON A R) (not (obs_1))))
)