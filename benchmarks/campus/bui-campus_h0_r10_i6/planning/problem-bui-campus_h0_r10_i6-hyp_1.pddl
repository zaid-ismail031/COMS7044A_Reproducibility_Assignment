(define (problem bui-campus_generic_hyp-0_10_6)
(:domain campus)
(:objects
)
(:init
(= (total-cost) 0)
(at hayman_theater)
)
(:goal
(and
(group-meeting-2) (banking) (lecture-3-taken) (lecture-4-taken) (group-meeting-3) (lunch)
)
)
(:metric minimize (total-cost))
)
