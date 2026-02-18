from rest_framework import permissions


class IsCustomerOwner(permissions.BasePermission):
    """
    Custom permission to only allow access to the owner of the customer record.
    Assumes the model has a 'customer' FK which has a 'user' OneToOneField.
    Or if the object is a Customer itself.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # Wait, for private data we want to restrict read access too!
        
        if request.user.is_staff:
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user
        
        if hasattr(obj, "customer"):
            if hasattr(obj.customer, "user"):
                return obj.customer.user == request.user
            
        # For deeper nesting like Meter -> Property -> Customer
        if hasattr(obj, "property") and hasattr(obj.property, "customer"):
             if hasattr(obj.property.customer, "user"):
                return obj.property.customer.user == request.user

        # For MeterReading -> Meter -> Property -> Customer
        if hasattr(obj, "meter") and hasattr(obj.meter, "property"):
             if hasattr(obj.meter.property.customer, "user"):
                return obj.meter.property.customer.user == request.user
                
        return False
