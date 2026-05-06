(define (problem bui-campus_generic_hyp-1_10_1)
(:domain campus)
(:objects
)
(:init
(= (total-cost) 0)
(at cbs)
)
(:goal
(and
(group-meeting-2) (banking) (lecture-3-taken) (lecture-4-taken) (group-meeting-3) (lunch)
)
)
(:metric minimize (total-cost))
)
