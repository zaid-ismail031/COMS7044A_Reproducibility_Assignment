(define (problem bui-campus_generic_hyp-0_50_3)
(:domain campus)
(:objects
)
(:init
(= (total-cost) 0)
(at psychology_bldg)
)
(:goal
(and
(group-meeting-2) (banking) (lecture-3-taken) (lecture-4-taken) (group-meeting-3) (lunch)
)
)
(:metric minimize (total-cost))
)
