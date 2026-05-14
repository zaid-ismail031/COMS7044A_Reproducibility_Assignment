(define (problem bui-campus_generic_hyp-1_70_36)
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
