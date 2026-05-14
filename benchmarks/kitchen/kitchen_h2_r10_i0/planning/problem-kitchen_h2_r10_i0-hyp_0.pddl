(define (problem kitchen_generic_hyp-2_10_0)
(:domain kitchen)
(:objects
)
(:init
(= (total-cost) 0)
(dummy)
)
(:goal
(and
(made_breakfast)
)
)
(:metric minimize (total-cost))
)
