# User and permission must be in security subdomain at same bounded context
# It would be named as Identity/Acess Context with shared kernel for other context like the customer

# Context map helps communicate with different bounded contexts

# Customer must be independent from user. That helps be a customer in separated role also
class Customer:
    pass
