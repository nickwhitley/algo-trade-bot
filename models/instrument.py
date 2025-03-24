class Instrument:
    def __init__(self, name, type, displayName, pipLocation, tradeUnitsPrecision, marginRate):
        self.name = name
        self.type = type
        self.displayName = displayName
        self.pipLocation = pow(10, pipLocation)
        self.tradeUnitsPrecision = tradeUnitsPrecision
        self.marginRate = float(marginRate)

    def __repr__(self):
        return str(vars(self))

    @classmethod
    def from_api_object(cls, obj):
        return Instrument(
            obj['name'],
            obj['type'],
            obj['displayName'],
            obj['pipLocation'],
            obj['tradeUnitsPrecision'],
            obj['marginRate']
        )