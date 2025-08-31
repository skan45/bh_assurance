import { Clock, FileText, Car, MapPin, Phone, Package } from "lucide-react";

const timelineItems = [
  {
    period: "AUJOURD'HUI",
    items: [
      { icon: FileText, text: "Paiements de mes contrats" },
      { icon: Car, text: "Garanties de mon assurance automobile" },
    ]
  },
  {
    period: "HIER", 
    items: [
      { icon: Clock, text: "Délai d'indemnisation après sinistre" },
      { icon: FileText, text: "Mon dernier sinistre déclaré" },
      { icon: FileText, text: "Exclusions de la garantie décès" },
      { icon: MapPin, text: "Trouver une agence BH Assurances" },
    ]
  },
  {
    period: "SEMAINE DERNIÈRE",
    items: [
      { icon: MapPin, text: "Trouver une agence BH Assurances" },
      { icon: Phone, text: "Contacter un conseiller client" },
      { icon: Package, text: "Produits et offres disponibles" },
    ]
  }
];

const Sidebar = () => {
  return (
    <aside className="w-80 bg-sidebar-bg border border-border h-full flex flex-col m-2 shadow-sm">
      {/* Timeline Items */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {timelineItems.map((timeline, timelineIndex) => (
          <div key={timelineIndex} className="space-y-3">
            <h3 className="text-xs font-medium text-muted-foreground tracking-wide">
              {timeline.period}
            </h3>
            <div className="space-y-2">
              {timeline.items.map((item, itemIndex) => (
                <div
                  key={itemIndex}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
                >
                  <item.icon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-foreground">{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;