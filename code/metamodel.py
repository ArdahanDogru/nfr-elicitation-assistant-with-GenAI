from typing import List, Dict, Any, Optional
from enum import Enum
import inspect
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# ============================================================================
# LEVEL 1: METAMODEL (Ontology) - METACLASSES
# ============================================================================

class PropositionMetaClass(type):
    pass
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Always create new set (don't share with parent)
        parent_attrs = set()
        if hasattr(cls, '_metaclass_attributes'):
            parent_attrs = cls._metaclass_attributes.copy()
        cls._metaclass_attributes = parent_attrs | {'priority', 'label'}
        return cls


class SoftgoalMetaClass(PropositionMetaClass):
    pass
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        parent_attrs = set()
        if hasattr(cls, '_metaclass_attributes'):
            parent_attrs = cls._metaclass_attributes.copy()
        # Create new set with parent + new attributes
        cls._metaclass_attributes = parent_attrs | {'type', 'topic','statement'}
        return cls


class NFRSoftgoalMetaClass(SoftgoalMetaClass):
    pass


class OperationalizingSoftgoalMetaClass(SoftgoalMetaClass):
    pass

class ClaimSoftgoalMetaClass(SoftgoalMetaClass):
    pass
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # ClaimSoftgoal has ONLY argument attribute
        cls._metaclass_attributes = {'argument'}
        return cls


class SoftgoalTypeMetaClass(type):
    pass

class SoftgoalTopicMetaClass(type):
    pass

class ContributionMetaClass(PropositionMetaClass):
    pass

class MethodMetaClass(type):
    pass

class DecompositionMethodMetaClass(MethodMetaClass):
    pass

class NFRDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    pass

class OperationalizationDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    pass
class ClaimDecompositionMethodMetaClass(DecompositionMethodMetaClass):
    pass


# ============================================================================
# LEVEL 2: MODEL - CLASSES
# ============================================================================

# ----------------------------------------------------------------------------
# Enums and Base Types
# ----------------------------------------------------------------------------

class PropositionPriority(Enum):
    pass
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class PropositionLabel(Enum):
    pass
    SATISFICED = "satisficed"
    DENIED = "denied"
    WEAKLY_SATISFICED = "weakly_satisficed"
    WEAKLY_DENIED = "weakly_denied"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class ContributionType(Enum):
    pass
    MAKE = "MAKE"
    HELP = "HELP"
    SOME_PLUS = "SOME+"
    UNKNOWN = "UNKNOWN"
    SOME_MINUS = "SOME-"
    HURT = "HURT"
    BREAK = "BREAK"
    CLAIM = "CLAIM"  # Claim argues for/supports a target


# ----------------------------------------------------------------------------
# Base Classes
# ----------------------------------------------------------------------------

class Proposition(metaclass=PropositionMetaClass):
    pass
    def __init__(self):
        self.priority = PropositionPriority.MEDIUM
        self.label = PropositionLabel.UNKNOWN


class Softgoal(Proposition, metaclass=SoftgoalMetaClass):
    pass
    def __init__(self):
        super().__init__()
        self.type = None
        self.topic = None
        self.statement = None


class NFRSoftgoal(Softgoal, metaclass=NFRSoftgoalMetaClass):
    pass


class OperationalizingSoftgoal(Softgoal, metaclass=OperationalizingSoftgoalMetaClass):
    pass


class ClaimSoftgoal(Softgoal, metaclass=ClaimSoftgoalMetaClass):
    pass
    def __init__(self, argument: str = "",  supports=None):
        # Don't call super().__init__() to avoid getting label, priority
        self.argument = argument
        self.supports = supports

class SoftgoalTopic:
    pass
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"SoftgoalTopic('{self.name}')"


# ----------------------------------------------------------------------------
# Softgoal Type Classes
# ----------------------------------------------------------------------------

class SoftgoalType(metaclass=SoftgoalTypeMetaClass):
    pass

class NFRSoftgoalType(SoftgoalType):
    pass


class OperationalizingSoftgoalType(SoftgoalType):
    pass

'''
class ClaimSoftgoalType(SoftgoalType):
    pass


# Specific Claim Types (the claim is the type itself)
class SmithPerformanceClaimType(ClaimSoftgoalType):
    pass
    topic = "According to Smith's User-Centered Performance Metrics"


class CIATriadClaimType(ClaimSoftgoalType):
    pass
    topic = "Trusted Computer System Evaluation Criteria (TCSEC/Orange Book, 1985) - Defines security through Confidentiality, Integrity, and Availability"


class WindowsTaskManagerClaimType(ClaimSoftgoalType):
    pass
    topic = "Microsoft Windows Task Manager - Performance Tab"


class TraditionalCSPerformanceClaimType(ClaimSoftgoalType):
    pass
    topic = "Traditional Computer Science - Time and Space Complexity"

class WikipediaEncryptionTypesClaimType(ClaimSoftgoalType):
    pass
    topic = "Wikipedia (Encryption article) - Classifies encryption into Symmetric-key and Public-key (asymmetric) schemes"

class ChungNFRFrameworkClaimType(ClaimSoftgoalType):
    pass
    topic = "According to Chung et al.'s NFR Framework (2000)"

class ISO25010UsabilityClaimType(ClaimSoftgoalType):
    pass
    topic = "ISO/IEC 25010:2011 Systems and software Quality Requirements and Evaluation (SQuaRE) - Defines usability through five quality sub-characteristics"

class ManduchiSafetyClaimType(ClaimSoftgoalType):
    pass
    topic = "Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users. ACM Transactions on Accessible Computing - Advance warnings minimize input to focus on safety"

class ManduchiUsabilityClaimType(ClaimSoftgoalType):
    pass
    topic = "Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users - Multimodal feedback enables hands-free operation"

class ASSISTUsabilityClaimType(ClaimSoftgoalType):
    pass
    topic = "ASSIST (2020). Indoor navigation assistant for blind and visually impaired people - Personalized interfaces improve usability by adapting to unique user experiences"

class PMCCognitiveLoadClaimType(ClaimSoftgoalType):
    pass
    topic = "PMC (2024). Comprehensive review on NUI, multi-sensory interfaces for visually impaired users - Concise audio reduces cognitive overburden"

class PMCReceptivityClaimType(ClaimSoftgoalType):
    pass
    topic = "PMC (2024). Comprehensive review on NUI, multi-sensory interfaces for visually impaired users - Non-speech sounds improve receptivity"

class SensorsSafetyClaimType(ClaimSoftgoalType):
    pass
    topic = "Sensors (2012). An Indoor Navigation System for the Visually Impaired - Positioning accuracy of ≤0.4m enables safe navigation"

class PouloseSensorFusionClaimType(ClaimSoftgoalType):
    pass
    topic = "Poulose & Kim (2019). A Sensor Fusion Framework for Indoor Localization Using Smartphone Sensors - Sensor fusion reduces positioning error to 0.44-1.17m"

class NielsenLearnabilityClaimType(ClaimSoftgoalType):
    pass
    topic = "Nielsen Norman Group (2019). How to Measure Learnability of a User Interface - Steep learning curves enable proficiency within approximately 4 trials"

class MolichNielsen1990ACMClaimType(ClaimSoftgoalType):
    """Original 9 usability heuristics - Journal publication"""
    pass
    topic = "Molich, R., and Nielsen, J. (1990). Improving a human-computer dialogue. Communications of the ACM, 33(3), pp. 338-348"


class NielsenMolich1990CHIClaimType(ClaimSoftgoalType):
    """Original 9 usability heuristics - Conference publication"""
    pass
    topic = "Nielsen, J., and Molich, R. (1990). Heuristic evaluation of user interfaces. Proc. ACM CHI'90 Conf. (Seattle, WA, 1-5 April), pp. 249-256"


class Nielsen1993BookClaimType(ClaimSoftgoalType):
    """Extended 10 usability heuristics - Book"""
    pass
    topic = "Nielsen, J. (1993). Usability Engineering. Academic Press, Boston, MA"
'''

# NFR Quality Attribute Types
class PerformanceType(NFRSoftgoalType):
    pass


class TimePerformanceType(NFRSoftgoalType):
    pass


class SpacePerformanceType(NFRSoftgoalType):
    pass


class ResponsivenessPerformanceType(NFRSoftgoalType):
    pass

class UbiquitousType(NFRSoftgoalType):
    pass

class OperationalType(NFRSoftgoalType):
    pass

# Windows Task Manager Performance Types
class CPUUtilizationType(NFRSoftgoalType):
    pass


class MemoryUsageType(NFRSoftgoalType):
    pass


class DiskTimeType(NFRSoftgoalType):
    pass


class NetworkThroughputType(NFRSoftgoalType):
    pass


class GPUUtilizationType(NFRSoftgoalType):
    pass


class SecurityType(NFRSoftgoalType):
    pass


class ConfidentialityType(NFRSoftgoalType):
    pass


class IntegrityType(NFRSoftgoalType):
    pass


class AvailabilityType(NFRSoftgoalType):
    pass


class UsabilityType(NFRSoftgoalType):
    pass


class ReliabilityType(NFRSoftgoalType):
    pass


class MaintainabilityType(NFRSoftgoalType):
    pass


# Additional NFR Quality Attribute Types (alphabetically ordered)
class AccuracyType(NFRSoftgoalType):
    pass


class AdaptabilityType(NFRSoftgoalType):
    pass


class BiasType(NFRSoftgoalType):
    pass


class CompletenessType(NFRSoftgoalType):
    pass


class ComplexityType(NFRSoftgoalType):
    pass


class ConsistencyType(NFRSoftgoalType):
    pass


class CorrectnessType(NFRSoftgoalType):
    pass


class DomainAdaptationType(NFRSoftgoalType):
    pass


class EfficiencyType(NFRSoftgoalType):
    pass


class EthicsType(NFRSoftgoalType):
    pass


class ExplainabilityType(NFRSoftgoalType):
    pass


class FairnessType(NFRSoftgoalType):
    pass


class FaultToleranceType(NFRSoftgoalType):
    pass


class FlexibilityType(NFRSoftgoalType):
    pass


class InterpretabilityType(NFRSoftgoalType):
    pass


class InteroperabilityType(NFRSoftgoalType):
    pass


class JustifiabilityType(NFRSoftgoalType):
    pass


class PortabilityType(NFRSoftgoalType):
    pass


class PrivacyType(NFRSoftgoalType):
    pass


class RepeatabilityType(NFRSoftgoalType):
    pass


class RetrainabilityType(NFRSoftgoalType):
    pass


class ReproducibilityType(NFRSoftgoalType):
    pass


class ReusabilityType(NFRSoftgoalType):
    pass


class SafetyType(NFRSoftgoalType):
    pass


class ScalabilityType(NFRSoftgoalType):
    pass


class TestabilityType(NFRSoftgoalType):
    pass


class TransparencyType(NFRSoftgoalType):
    pass


class TraceabilityType(NFRSoftgoalType):
    pass


class TrustType(NFRSoftgoalType):
    pass


class LegalComplianceType(NFRSoftgoalType):
    pass


class LookFeelType(NFRSoftgoalType):
    pass

# New NFR Types from Taxonomy
class RecoverabilityType(NFRSoftgoalType):
    pass

class DiagnosabilityType(NFRSoftgoalType):
    pass

class CompatibilityType(NFRSoftgoalType):
    pass

class DeterministicBehaviorType(NFRSoftgoalType):
    pass

class LearnabilityType(NFRSoftgoalType):
    pass

class MemorabilityType(NFRSoftgoalType):
    pass

class ErrorPreventionType(NFRSoftgoalType):
    pass

class SatisfactionType(NFRSoftgoalType):
    pass

class SimpleNaturalDialogueType(NFRSoftgoalType):
    """Dialogues should not contain information which is irrelevant or rarely needed. 
    Every extra unit of information in a dialogue competes with the relevant units of 
    information and diminishes their relative visibility. All information should appear 
    in a natural and logical order."""
    pass

class UserLanguageType(NFRSoftgoalType):
    """The dialogue should be expressed clearly in words, phrases and concepts familiar 
    to the user, rather than in system-oriented terms."""
    pass


class MinimizeMemoryLoadType(NFRSoftgoalType):
    """The user should not have to remember information from one part of the dialogue 
    to another. Instructions for use of the system should be visible or easily 
    retrievable whenever appropriate."""
    pass


class FeedbackType(NFRSoftgoalType):
    """The system should always keep users informed about what is going on, through 
    appropriate feedback within reasonable time."""
    pass


class ClearlyMarkedExitsType(NFRSoftgoalType):
    """Users often choose system functions by mistake and will need a clearly marked 
    'emergency exit' to leave the unwanted state without having to go through an 
    extended dialogue."""
    pass


class ShortcutsType(NFRSoftgoalType):
    """Accelerators—unseen by the novice user—may often speed up the interaction for 
    the expert user such that the system can cater to both inexperienced and 
    experienced users."""
    pass


class GoodErrorMessagesType(NFRSoftgoalType):
    """Error messages should be expressed in plain language (no codes), precisely 
    indicate the problem, and constructively suggest a solution."""
    pass




class HelpDocumentationType(NFRSoftgoalType):
    """Even though it is better if the system can be used without documentation, it 
    may be necessary to provide help and documentation. Any such information should 
    be easy to search, be focused on the user's task, list concrete steps to be 
    carried out, and not be too large."""
    pass



# Operationalizing Technique Types
class IndexingType(OperationalizingSoftgoalType):
    pass


class CachingType(OperationalizingSoftgoalType):
    pass


class EncryptionType(OperationalizingSoftgoalType):
    pass

class SymmetricKeyEncryptionType(EncryptionType):
    pass
    pass

class PublicKeyEncryptionType(EncryptionType):
    pass
    pass

class RSAEncryptionType(PublicKeyEncryptionType):
    pass
    pass

class AuditingType(OperationalizingSoftgoalType):
    pass

class ExceptionHandlingType(OperationalizingSoftgoalType):
    pass
    
class SearchType(OperationalizingSoftgoalType):
    pass


class DisplayType(OperationalizingSoftgoalType):
    pass


class RefreshType(OperationalizingSoftgoalType):
    pass


class LogType(OperationalizingSoftgoalType):
    pass

class AuthorizationType(OperationalizingSoftgoalType):
    pass

class AuthenticationType(OperationalizingSoftgoalType):
    pass

class AccessRuleValidationType(OperationalizingSoftgoalType):
    pass

class IdentificationType(OperationalizingSoftgoalType):
    pass


class SyncType(OperationalizingSoftgoalType):
    pass


class MonitorType(OperationalizingSoftgoalType):
    pass


class ValidationType(OperationalizingSoftgoalType):
    pass


class NotifyType(OperationalizingSoftgoalType):
    pass


class StoreType(OperationalizingSoftgoalType):
    pass


class ExportType(OperationalizingSoftgoalType):
    pass


class BackupType(OperationalizingSoftgoalType):
    pass


class CompressionType(OperationalizingSoftgoalType):
    pass

class LoadBalancingType(OperationalizingSoftgoalType):
    pass

class VirtualizationType(OperationalizingSoftgoalType):
    pass

class NetworkMonitoringType(OperationalizingSoftgoalType):
    pass

class DataWarehouseType(OperationalizingSoftgoalType):
    pass

class SimulationType(OperationalizingSoftgoalType):
    pass

class EarlyWarningType(OperationalizingSoftgoalType):
    pass

class MultimodalFeedbackType(OperationalizingSoftgoalType):
    pass

class PersonalizedInterfacesType(OperationalizingSoftgoalType):
    pass

class ConciseAudioInstructionsType(OperationalizingSoftgoalType):
    pass

class NonSpeechAudioCuesType(OperationalizingSoftgoalType):
    pass

class SubMeterPositioningType(OperationalizingSoftgoalType):
    pass

class SensorFusionType(OperationalizingSoftgoalType):
    pass

class RapidTaskMasteryType(OperationalizingSoftgoalType):
    pass


# ----------------------------------------------------------------------------
# Softgoal Classes (for creating instances)
# ----------------------------------------------------------------------------

class PerformanceSoftgoal(NFRSoftgoal):
    pass
    type = PerformanceType  # Class-level attribute


class TimePerformanceSoftgoal(NFRSoftgoal):
    pass
    type = TimePerformanceType


class SpacePerformanceSoftgoal(NFRSoftgoal):
    pass
    type = SpacePerformanceType


class ResponsivenessPerformanceSoftgoal(NFRSoftgoal):
    pass
    type = ResponsivenessPerformanceType


# Windows Task Manager Performance Softgoal Classes
class CPUUtilizationSoftgoal(NFRSoftgoal):
    pass
    type = CPUUtilizationType


class MemoryUsageSoftgoal(NFRSoftgoal):
    pass
    type = MemoryUsageType


class DiskTimeSoftgoal(NFRSoftgoal):
    pass
    type = DiskTimeType


class NetworkThroughputSoftgoal(NFRSoftgoal):
    pass
    type = NetworkThroughputType


class GPUUtilizationSoftgoal(NFRSoftgoal):
    pass
    type = GPUUtilizationType


class SecuritySoftgoal(NFRSoftgoal):
    pass
    type = SecurityType


class ConfidentialitySoftgoal(NFRSoftgoal):
    pass
    type = ConfidentialityType


class IntegritySoftgoal(NFRSoftgoal):
    pass
    type = IntegrityType


class AvailabilitySoftgoal(NFRSoftgoal):
    pass
    type = AvailabilityType


class UsabilitySoftgoal(NFRSoftgoal):
    pass
    type = UsabilityType


class ReliabilitySoftgoal(NFRSoftgoal):
    pass
    type = ReliabilityType


class MaintainabilitySoftgoal(NFRSoftgoal):
    pass
    type = MaintainabilityType


# Additional NFR Softgoal Classes (alphabetically ordered)
class AccuracySoftgoal(NFRSoftgoal):
    pass
    type = AccuracyType

class UbiquitousSoftgoal(NFRSoftgoal):
    pass
    type = UbiquitousType

class OperationalSoftgoal(NFRSoftgoal):
    pass
    type = OperationalType

class AdaptabilitySoftgoal(NFRSoftgoal):
    pass
    type = AdaptabilityType


class BiasSoftgoal(NFRSoftgoal):
    pass
    type = BiasType


class CompletenessSoftgoal(NFRSoftgoal):
    pass
    type = CompletenessType


class ComplexitySoftgoal(NFRSoftgoal):
    pass
    type = ComplexityType


class ConsistencySoftgoal(NFRSoftgoal):
    pass
    type = ConsistencyType


class CorrectnessSoftgoal(NFRSoftgoal):
    pass
    type = CorrectnessType


class DomainAdaptationSoftgoal(NFRSoftgoal):
    pass
    type = DomainAdaptationType


class EfficiencySoftgoal(NFRSoftgoal):
    pass
    type = EfficiencyType


class EthicsSoftgoal(NFRSoftgoal):
    pass
    type = EthicsType


class ExplainabilitySoftgoal(NFRSoftgoal):
    pass
    type = ExplainabilityType


class FairnessSoftgoal(NFRSoftgoal):
    pass
    type = FairnessType


class FaultToleranceSoftgoal(NFRSoftgoal):
    pass
    type = FaultToleranceType


class FlexibilitySoftgoal(NFRSoftgoal):
    pass
    type = FlexibilityType


class InterpretabilitySoftgoal(NFRSoftgoal):
    pass
    type = InterpretabilityType


class InteroperabilitySoftgoal(NFRSoftgoal):
    pass
    type = InteroperabilityType


class JustifiabilitySoftgoal(NFRSoftgoal):
    pass
    type = JustifiabilityType


class PortabilitySoftgoal(NFRSoftgoal):
    pass
    type = PortabilityType


class PrivacySoftgoal(NFRSoftgoal):
    pass
    type = PrivacyType


class RepeatabilitySoftgoal(NFRSoftgoal):
    pass
    type = RepeatabilityType


class RetrainabilitySoftgoal(NFRSoftgoal):
    pass
    type = RetrainabilityType


class ReproducibilitySoftgoal(NFRSoftgoal):
    pass
    type = ReproducibilityType


class ReusabilitySoftgoal(NFRSoftgoal):
    pass
    type = ReusabilityType


class SafetySoftgoal(NFRSoftgoal):
    pass
    type = SafetyType


class ScalabilitySoftgoal(NFRSoftgoal):
    pass
    type = ScalabilityType


class TestabilitySoftgoal(NFRSoftgoal):
    pass
    type = TestabilityType


class TransparencySoftgoal(NFRSoftgoal):
    pass
    type = TransparencyType


class TraceabilitySoftgoal(NFRSoftgoal):
    pass
    type = TraceabilityType


class TrustSoftgoal(NFRSoftgoal):
    pass
    type = TrustType


class LegalComplianceSoftgoal(NFRSoftgoal):
    pass
    type = LegalComplianceType


class LookFeelSoftgoal(NFRSoftgoal):
    pass
    type = LookFeelType

class RecoverabilitySoftgoal(NFRSoftgoal):
    pass
    type = RecoverabilityType

class DiagnosabilitySoftgoal(NFRSoftgoal):
    pass
    type = DiagnosabilityType

class CompatibilitySoftgoal(NFRSoftgoal):
    pass
    type = CompatibilityType

class DeterministicBehaviorSoftgoal(NFRSoftgoal):
    pass
    type = DeterministicBehaviorType    

class LearnabilitySoftgoal(NFRSoftgoal):
    pass
    type = LearnabilityType

class MemorabilitySoftgoal(NFRSoftgoal):
    pass
    type = MemorabilityType

class ErrorPreventionSoftgoal(NFRSoftgoal):
    pass
    type = ErrorPreventionType

class SatisfactionSoftgoal(NFRSoftgoal):
    pass
    type = SatisfactionType

class SimpleNaturalDialogueSoftgoal(NFRSoftgoal):
    pass
    type = SimpleNaturalDialogueType


class UserLanguageSoftgoal(NFRSoftgoal):
    pass
    type = UserLanguageType


class MinimizeMemoryLoadSoftgoal(NFRSoftgoal):
    pass
    type = MinimizeMemoryLoadType


# ConsistencySoftgoal already exists


class FeedbackSoftgoal(NFRSoftgoal):
    pass
    type = FeedbackType


class ClearlyMarkedExitsSoftgoal(NFRSoftgoal):
    pass
    type = ClearlyMarkedExitsType


class ShortcutsSoftgoal(NFRSoftgoal):
    pass
    type = ShortcutsType


class GoodErrorMessagesSoftgoal(NFRSoftgoal):
    pass
    type = GoodErrorMessagesType


# ErrorPreventionSoftgoal already exists


class HelpDocumentationSoftgoal(NFRSoftgoal):
    pass
    type = HelpDocumentationType


# Operationalizing Technique Softgoal Classes   

class IndexingSoftgoal(OperationalizingSoftgoal):
    pass
    type = IndexingType


class CachingSoftgoal(OperationalizingSoftgoal):
    pass
    type = CachingType


class EncryptionSoftgoal(OperationalizingSoftgoal):
    pass
    type = EncryptionType

class SymmetricKeyEncryptionSoftgoal(EncryptionSoftgoal):
    pass
    type = SymmetricKeyEncryptionType

class PublicKeyEncryptionSoftgoal(EncryptionSoftgoal):
    pass
    type = PublicKeyEncryptionType

class RSAEncryptionSoftgoal(PublicKeyEncryptionSoftgoal):
    pass
    type = RSAEncryptionType



class AuditingSoftgoal(OperationalizingSoftgoal):
    pass
    type = AuditingType

class ExceptionHandlingSoftgoal(OperationalizingSoftgoal):
    pass
    type = ExceptionHandlingType

class SearchSoftgoal(OperationalizingSoftgoal):
    pass
    type = SearchType

class DisplaySoftgoal(OperationalizingSoftgoal):
    pass
    type = DisplayType


class RefreshSoftgoal(OperationalizingSoftgoal):
    pass
    type = RefreshType


class LogSoftgoal(OperationalizingSoftgoal):
    pass
    type = LogType


class AuthenticationSoftgoal(OperationalizingSoftgoal):
    pass
    type = AuthenticationType

class AuthorizationSoftgoal(OperationalizingSoftgoal):
    pass
    type = AuthorizationType

class AccessRuleValidationSoftgoal(OperationalizingSoftgoal):
    pass
    type = AccessRuleValidationType

class IdentificationSoftgoal(OperationalizingSoftgoal):
    pass
    type = IdentificationType

class SyncSoftgoal(OperationalizingSoftgoal):
    pass
    type = SyncType


class MonitorSoftgoal(OperationalizingSoftgoal):
    pass
    type = MonitorType


class ValidationSoftgoal(OperationalizingSoftgoal):
    pass
    type = ValidationType


class NotifySoftgoal(OperationalizingSoftgoal):
    pass
    type = NotifyType


class StoreSoftgoal(OperationalizingSoftgoal):
    pass
    type = StoreType


class ExportSoftgoal(OperationalizingSoftgoal):
    pass
    type = ExportType


class BackupSoftgoal(OperationalizingSoftgoal):
    pass
    type = BackupType

class CompressionSoftgoal(OperationalizingSoftgoal):
    pass
    type = CompressionType

class LoadBalancingSoftgoal(OperationalizingSoftgoal):
    pass
    type = LoadBalancingType

class VirtualizationSoftgoal(OperationalizingSoftgoal):
    pass
    type = VirtualizationType

class NetworkMonitoringSoftgoal(OperationalizingSoftgoal):
    pass
    type = NetworkMonitoringType

class DataWarehouseSoftgoal(OperationalizingSoftgoal):
    pass
    type = DataWarehouseType

class SimulationSoftgoal(OperationalizingSoftgoal): 
    pass
    type = SimulationType

class EarlyWarningSoftgoal(OperationalizingSoftgoal):
    pass
    type = EarlyWarningType

class MultimodalFeedbackSoftgoal(OperationalizingSoftgoal):
    pass
    type = MultimodalFeedbackType

class PersonalizedInterfacesSoftgoal(OperationalizingSoftgoal):
    pass
    type = PersonalizedInterfacesType

class ConciseAudioInstructionsSoftgoal(OperationalizingSoftgoal):
    pass
    type = ConciseAudioInstructionsType

class NonSpeechAudioCuesSoftgoal(OperationalizingSoftgoal):
    pass
    type = NonSpeechAudioCuesType

class SubMeterPositioningSoftgoal(OperationalizingSoftgoal):
    pass
    type = SubMeterPositioningType

class SensorFusionSoftgoal(OperationalizingSoftgoal):
    pass
    type = SensorFusionType

class RapidTaskMasterySoftgoal(OperationalizingSoftgoal):
    pass
    type = RapidTaskMasteryType

# ----------------------------------------------------------------------------
# Method Classes
# ----------------------------------------------------------------------------

class Method(metaclass=MethodMetaClass):
    pass
    pass


class DecompositionMethod(Method, metaclass=DecompositionMethodMetaClass):
    pass
    def __init__(self, name: str, parent, offspring: List):
        self.name = name
        self.parent = parent  # Parent type being decomposed
        self.offspring = offspring  # List of child types
    
    def __repr__(self):
        parent_name = self.parent.__name__ if hasattr(self.parent, '__name__') else str(self.parent)
        offspring_names = [o.__name__ if hasattr(o, '__name__') else str(o) for o in self.offspring]
        return f"DecompositionMethod('{self.name}', {parent_name} → {offspring_names})"

class NFRDecompositionMethod(DecompositionMethod, metaclass=NFRDecompositionMethodMetaClass):
    pass

class PerformanceDecompositionMethod(NFRDecompositionMethod):
    pass
    parent = PerformanceType

class SecurityDecompositionMethod(NFRDecompositionMethod):
    pass
    parent = SecurityType

class UsabilityDecompositionMethod(NFRDecompositionMethod):
    pass
    parent = UsabilityType


class OperationalizationDecompositionMethod(DecompositionMethod, metaclass=OperationalizationDecompositionMethodMetaClass):
    pass

class AuthorizationDecompositionMethod(OperationalizationDecompositionMethod):
    pass
    parent = AuthorizationType

class ClaimDecompositionMethod(DecompositionMethod, metaclass=ClaimDecompositionMethodMetaClass):
    pass


class Contribution(Proposition, metaclass=ContributionMetaClass):
    pass
    def __init__(self, source_name: str, target_name: str, contribution_type: ContributionType):
        super().__init__()
        self.source = source_name
        self.target = target_name
        self.type = contribution_type
    



# ============================================================================
# LEVEL 3: GROUND INSTANCES
# ============================================================================

print("  [OK] Level 1 (Metamodel): Metaclasses defined")
print("  [OK] Level 2 (Model): Classes defined")

# ----------------------------------------------------------------------------
# Decomposition Method Instances (NO source attribute!)
# ----------------------------------------------------------------------------

# Performance decomposition - Traditional CS approach
PerformanceDecomp1 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 1",
    parent=PerformanceType,
    offspring=[TimePerformanceType, SpacePerformanceType]
)

# Performance decomposition - Smith's approach
PerformanceDecomp2 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 2",
    parent=PerformanceType,
    offspring=[TimePerformanceType, SpacePerformanceType, ResponsivenessPerformanceType]
)

# Performance decomposition - Windows Task Manager approach
PerformanceDecomp3 = PerformanceDecompositionMethod(
    name="Performance Type Decomposition 3",
    parent=PerformanceType,
    offspring=[CPUUtilizationType, MemoryUsageType, DiskTimeType, NetworkThroughputType, GPUUtilizationType]
)

# Security decomposition - CIA Triad
SecurityDecomp1 = SecurityDecompositionMethod(
    name="Security Type Decomposition 1",
    parent=SecurityType,
    offspring=[ConfidentialityType, IntegrityType, AvailabilityType]
)



AuthorizationDecomp1 = AuthorizationDecompositionMethod(
    name="Authorization Type Decomposition 1",
    parent=AuthorizationType,
    offspring=[IdentificationType, AuthenticationType, AccessRuleValidationType]
)

UsabilityDecomp_ISO25010 = UsabilityDecompositionMethod(
    name="ISO 25010 Usability Decomposition",
    parent=UsabilityType,
    offspring=[LearnabilityType, EfficiencyType, MemorabilityType, ErrorPreventionType, SatisfactionType]
)

UsabilityDecomp_Nielsen = UsabilityDecompositionMethod(
    name = "Molich & Nielsen's Original 9 Usability Heuristics (1990)",
    parent = UsabilityType,
    offspring = [
        SimpleNaturalDialogueType,    # H1: Simple and natural dialogue
        UserLanguageType,              # H2: Speak the user's language
        MinimizeMemoryLoadType,        # H3: Minimize the users' memory load
        ConsistencyType,               # H4: Consistency
        FeedbackType,                  # H5: Feedback
        ClearlyMarkedExitsType,        # H6: Clearly marked exits
        ShortcutsType,                 # H7: Shortcuts
        GoodErrorMessagesType,         # H8: Good error messages
        ErrorPreventionType            # H9: Prevent errors
    ]
)

UsabilityDecomp_NielsenAndMolich = UsabilityDecompositionMethod(

    name = "Nielsen's Extended 10 Usability Heuristics (1993)",
    parent = UsabilityType,
    offspring = [
        SimpleNaturalDialogueType,    # H1: Simple and natural dialogue
        UserLanguageType,              # H2: Speak the user's language
        MinimizeMemoryLoadType,        # H3: Minimize the users' memory load
        ConsistencyType,               # H4: Consistency
        FeedbackType,                  # H5: Feedback
        ClearlyMarkedExitsType,        # H6: Clearly marked exits
        ShortcutsType,                 # H7: Shortcuts
        GoodErrorMessagesType,         # H8: Good error messages
        ErrorPreventionType,           # H9: Prevent errors
        HelpDocumentationType          # H10: Help and documentation (NEW in 1993)
    ]
)

# ----------------------------------------------------------------------------
# ClaimSoftgoal Instances (Attribution & Argumentation)
# ----------------------------------------------------------------------------

# Claim Softgoals (using argument attribute)
claim_traditional_cs = ClaimSoftgoal(
    argument="Traditional Computer Science - Time and Space Complexity",
    supports= PerformanceDecomp1)

claim_smith = ClaimSoftgoal(
    argument="According to Smith's User-Centered Performance Metrics",
    supports = PerformanceDecomp2)

claim_windows = ClaimSoftgoal(
    argument="Microsoft Windows Task Manager - Performance Tab",
    supports= PerformanceDecomp3)

claim_tcsec = ClaimSoftgoal(
    argument="Trusted Computer System Evaluation Criteria (TCSEC/Orange Book, 1985) - Defines security through Confidentiality, Integrity, and Availability",
    supports = SecurityDecomp1)


claim_iso25010 = ClaimSoftgoal(
    argument="ISO/IEC 25010:2011 Systems and software Quality Requirements and Evaluation (SQuaRE) - Defines usability through five quality sub-characteristics",
    supports= UsabilityDecomp_ISO25010)

claim_nielsen_molich_1990 = ClaimSoftgoal(
    argument= "Molich, R., and Nielsen, J. (1990). Improving a human-computer dialogue. Communications of the ACM, 33(3), pp. 338-348",
    supports=UsabilityDecomp_NielsenAndMolich)

claim_nielsen_1993 = ClaimSoftgoal(
    argument= "Nielsen, J. (1993). Usability Engineering. Academic Press, Boston, MA",
    supports=UsabilityDecomp_Nielsen)

# Additional claims for operationalizations
claim_manduchi_safety = ClaimSoftgoal(
    argument="Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users - Advance warnings minimize input to focus on safety",
    supports= NotifyType)

claim_manduchi_usability = ClaimSoftgoal(
    argument="Manduchi et al. (2024). Smartphone apps for indoor wayfinding for blind users - Multimodal feedback enables hands-free operation",
    supports=DisplayType)


# ----------------------------------------------------------------------------
# NFR Softgoal Instances (Examples)
# ----------------------------------------------------------------------------



# Example 2: Specific security NFR using CIA triad
confidentialityNFR1 = ConfidentialitySoftgoal()
confidentialityNFR1.priority = PropositionPriority.CRITICAL
confidentialityNFR1.label = PropositionLabel.SATISFICED

# Example 3: 
pgp_implementation = PublicKeyEncryptionType()
pgp_implementation.type = PublicKeyEncryptionType  # Or a more specific type
pgp_implementation.is_ground_instance = True  # If you have this flag

# --- Performance Requirements ---
performanceNFR1 = PerformanceSoftgoal()
performanceNFR1.statement = "The product shall respond fast to keep up-to-date data in the display."

performanceNFR2 = PerformanceSoftgoal()
performanceNFR2.statement = "The system shall refresh the display every 60 seconds."

# --- Usability Requirements ---
usabilityNFR1 = UsabilitySoftgoal()
usabilityNFR1.statement = "The product shall be intuitive and self-explanatory."

usabilityNFR2 = UsabilitySoftgoal()
usabilityNFR2.statement = "The system shall be easy to use by the Program Administrators/Nursing Staff Members."

# --- Security Requirements ---
securityNFR1 = SecuritySoftgoal()
securityNFR1.statement = "Only registered realtors shall be able to access the system."

securityNFR2 = SecuritySoftgoal()
securityNFR2.statement = "The system shall be built such that it is as secure as possible from malicious interference."

# --- Operational Requirements ---
operationalNFR1 = OperationalSoftgoal()
operationalNFR1.statement = "The product shall adhere to the corporate Architecture guidelines."

# --- Look & Feel Requirements ---
lookFeelNFR1 = LookFeelSoftgoal()
lookFeelNFR1.statement = "The product shall comply with corporate User Interface Guidelines."

lookFeelNFR2 = LookFeelSoftgoal()
lookFeelNFR2.statement = "The appearance of the product shall appear professional."

# --- Portability Requirements ---
portabilityNFR1 = PortabilitySoftgoal()
portabilityNFR1.statement = "The system shall operate on Unix and Windows operating systems."

# --- Legal Requirements ---
legalNFR1 = LegalComplianceSoftgoal()
legalNFR1.statement = "All actions that modify an existing dispute case must be recorded in the case history."

# --- Availability Requirements ---
availabilityNFR1 = AvailabilitySoftgoal()
availabilityNFR1.statement = "The system shall be available to the users 24 hours a day, 7 days a week."

# --- Maintainability Requirements ---
maintainabilityNFR1 = MaintainabilitySoftgoal()
maintainabilityNFR1.statement = "The system should be easy enough to maintain that someone else could do it with a manual and a few hours training."
EarlyWarningToSafety = Contribution("EarlyWarning", "Safety", ContributionType.HELP)






# ----------------------------------------------------------------------------
# Contribution Instances (Examples)
# ----------------------------------------------------------------------------

# ops for perf => timeperf + perf + others


# ops for timeperf
IndexingToTimePerformance = Contribution("Indexing", "TimePerformance", ContributionType.HELP)
CachingToTimePerformance = Contribution("Caching", "TimePerformance", ContributionType.HELP)
EncryptionToTimePerformance = Contribution("Encryption", "TimePerformance", ContributionType.HURT)
CompressionToPerformance = Contribution("Compression", "TimePerformance", ContributionType.HELP)
NetworkMonitoringToTimePerformance = Contribution("NetworkMonitoring", "TimePerformance", ContributionType.HURT) # Packet inspection overhead
AuthenticationToTimePerformance = Contribution("Authentication", "TimePerformance", ContributionType.HURT) 

#ops for spacePerf
IndexingToSpacePerformance = Contribution("Indexing", "SpacePerformance", ContributionType.HURT)
CachingToSpacePerformance = Contribution("Caching", "SpacePerformance", ContributionType.HURT)
CompressionToSpacePerformance = Contribution("Compression", "SpacePerformance", ContributionType.HELP)

#ops for confidentiality
AuthenticationToConfidentiality = Contribution("Authentication", "Confidentiality", ContributionType.HELP)
EncryptionToConfidentiality = Contribution("Encryption", "Confidentiality", ContributionType.HELP)
NetworkMonitoringToConfidentiality = Contribution("NetworkMonitoring", "Confidentiality", ContributionType.HELP)
AccessRuleValidationToConfidentiality = Contribution("AccessRuleValidation", "Confidentiality", ContributionType.HELP)
AuthorizationToConfidentiality = Contribution("Authorization", "Confidentiality", ContributionType.HELP)

#ops for security
AuthenticationToSecurity = Contribution("Authentication", "Security", ContributionType.HELP)
EncryptionToSecurity = Contribution("Encryption", "Security", ContributionType.HELP)
NetworkMonitoringToSecurity = Contribution("NetworkMonitoring", "Security", ContributionType.HELP)

#ops for integrity
AuthenticationToIntegrity = Contribution("Authentication", "Integrity", ContributionType.HELP)

#ops for accuracy
AuditingToAccuracy = Contribution("Auditing", "Accuracy", ContributionType.HELP)
AuditingToSecurity = Contribution("Auditing", "Security", ContributionType.HELP)
ValidationToAccuracy = Contribution("Validation", "Accuracy", ContributionType.HELP)
ExceptionHandlingToAccuracy = Contribution("ExceptionHandling", "Accuracy", ContributionType.HELP)
SensorFusionToAccuracy = Contribution("SensorFusion", "Accuracy", ContributionType.HELP)

#ops for scalability
LoadBalancingToScalability = Contribution("LoadBalancing", "Scalability", ContributionType.HELP)

#ops for consistency
CachingToConsistency = Contribution("Caching", "Consistency", ContributionType.HURT)


#ops for portability
VirtualizationToPortability = Contribution("Virtualization", "Portability", ContributionType.HELP)

#ops for diagnosability and recoverability
LoggingToDiagnosability = Contribution("Logging", "Diagnosability", ContributionType.HELP)
BackupToRecoverability = Contribution("Backup", "Recoverability", ContributionType.MAKE)

#ops for usability
MultimodalFeedbackToUsability = Contribution("MultimodalFeedback", "Usability", ContributionType.HELP)
PersonalizedInterfacesToUsability = Contribution("PersonalizedInterfaces", "Usability", ContributionType.HELP)
ConciseAudioInstructionsToUsability = Contribution("ConciseAudioInstructions", "Usability", ContributionType.HELP)
NonSpeechAudioCuesToUsability = Contribution("NonSpeechAudioCues", "Usability", ContributionType.HELP)
AuthenticationToUsability = Contribution("Authentication", "Usability", ContributionType.HURT) 

#ops for safety
SubMeterPositioningToSafety = Contribution("SubMeterPositioning", "Safety", ContributionType.HELP)

#learnability
RapidTaskMasteryToLearnability = Contribution("RapidTaskMastery", "Learnability", ContributionType.MAKE)

print("  [OK] Level 3 (Ground Instances): Instances created")
print()

# ============================================================================
# SUMMARY
# ============================================================================

print("="*70)
print("NFR FRAMEWORK V2 - CLAIMSOFTGOAL APPROACH")
print("="*70)
print()
print("LEVEL 1 (Metaclasses):")
print("  • PropositionMetaClass")
print("  • SoftgoalMetaClass → [NFRSoftgoalMetaClass, OperationalizingSoftgoalMetaClass, ClaimSoftgoalMetaClass]")
print("  • SoftgoalTypeMetaClass")
print("  • DecompositionMethodMetaClass")
print()
print("LEVEL 2 (Classes/Types):")
print("  • SoftgoalType:")
print("    - NFRSoftgoalType: PerformanceType, SecurityType, etc.")
print("    - OperationalizingSoftgoalType: IndexingType, CachingType, etc.")
print("  • Softgoal:")
print("    - NFRSoftgoal: PerformanceSoftgoal, SecuritySoftgoal, etc.")
print("    - OperationalizingSoftgoal: IndexingSoftgoal, CachingSoftgoal, etc.")
print("    - ClaimSoftgoal (for argumentation)")
print("  • DecompositionMethod (NO source attribute)")
print()
print("LEVEL 3 (Ground Instances):")
print("  • 4 DecompositionMethod instances (Traditional CS, Smith, CIA Triad, Windows Task Manager)")
print("  • 4 ClaimSoftgoal instances (with attribution & justification)")
print()
print("KEY DESIGN DECISION:")
print("  [OK] DecompositionMethod has NO source attribute, ALL attribution via ClaimSoftgoals")
print()
print("="*70)
print("✅ 3-Level Metamodel V2 Successfully Built!")
print("="*70)